import os
import shutil
from groq import Groq
from tools.file_tools import move_file, create_folder, add_note, rename_file, delete_file
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json
import mimetypes
import ast
import re
import time
from tenacity import retry, stop_after_attempt, wait_exponential
import hashlib
import datetime
import zipfile

class FileOrganizer:
    def __init__(self, config):
        self.config = config
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.changes = []
        self.vectorizer = TfidfVectorizer(stop_words='english', min_df=1, max_df=0.9)
        self.vector_store = {}
        self.file_locations = {}
        self.dependencies = {}
        self.project_structure = {}
        mimetypes.init()

    def _is_processable_file(self, file_path):
        _, ext = os.path.splitext(file_path)
        processable_extensions = {
            '.txt', '.py', '.js', '.html', '.css', '.json', '.xml',
            '.md', '.csv', '.docx', '.xlsx', '.pdf', '.zip'
        }
        return ext.lower() in processable_extensions

    def _read_file(self, file_path):
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        try:
            if ext in ['.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.md', '.csv']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    return file.read()
            elif ext in ['.docx', '.xlsx', '.pdf']:
                # For these file types, we'll just return the file name and size as content
                file_size = os.path.getsize(file_path)
                return f"File: {os.path.basename(file_path)}, Size: {file_size} bytes"
            elif ext == '.zip':
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    return '\n'.join(zip_ref.namelist())
            else:
                return f"Unsupported file type: {ext}"
        except Exception as e:
            print(f"Error reading file {file_path}: {str(e)}")
            return None

    def _process_file(self, original_path, callback=None):
        current_path = self.file_locations.get(original_path)
        if not current_path or not os.path.exists(current_path):
            print(f"File no longer exists or has been moved: {current_path}")
            return
        
        if not self._is_processable_file(current_path):
            print(f"Skipping non-processable file: {current_path}")
            if callback:
                callback(f"Skipped: {current_path}")
            return

        file_content = self._read_file(current_path)
        if file_content is not None:
            category = self._categorize_file(current_path)
            response = self._get_ai_suggestion(current_path, file_content)
            if response:
                self._execute_suggestion(response, original_path)
            if callback:
                callback(f"Processed: {current_path}")
        else:
            print(f"Empty or unreadable file: {current_path}")
            if callback:
                callback(f"Skipped: {current_path}")

    def _categorize_file(self, file_path):
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        categories = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
            'document': ['.txt', '.docx', '.pdf', '.md'],
            'spreadsheet': ['.xlsx', '.csv'],
            'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c'],
            'data': ['.json', '.xml'],
            'archive': ['.zip', '.rar', '.7z']
        }
        for category, extensions in categories.items():
            if ext in extensions:
                return category
        return 'other'

    def _get_file_hash(self, file_path):
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def _find_duplicates(self):
        hashes = {}
        duplicates = []
        for file_path in self.file_locations.values():
            file_hash = self._get_file_hash(file_path)
            if file_hash in hashes:
                duplicates.append((file_path, hashes[file_hash]))
            else:
                hashes[file_hash] = file_path
        return duplicates

    def _analyze_file_content(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        analysis = {
            'word_count': len(re.findall(r'\w+', content)),
            'line_count': len(content.splitlines()),
            'has_urls': bool(re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)),
            'has_email': bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)),
        }
        return analysis

    def _create_backup(self, file_path):
        if os.path.isdir(file_path):
            print(f"Skipping backup for directory: {file_path}")
            return None
        try:
            backup_dir = os.path.join(os.path.dirname(file_path), '.file_organizer_backups')
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"{os.path.basename(file_path)}_{timestamp}")
            shutil.copy2(file_path, backup_path)
            return backup_path
        except PermissionError:
            print(f"Permission denied when creating backup for: {file_path}")
            return None
        except Exception as e:
            print(f"Error creating backup for {file_path}: {str(e)}")
            return None

    def _get_context(self, file_path):
        context = ""
        if file_path in self.dependencies:
            context += f"Dependencies: This file imports {', '.join(self.dependencies[file_path])}\n"
        
        rel_path = os.path.relpath(os.path.dirname(file_path), self.config.ROOT_PATH)
        if rel_path in self.project_structure:
            context += f"Project structure:\n"
            context += f"Current directory: {rel_path}\n"
            context += f"Files in this directory: {', '.join(self.project_structure[rel_path]['files'])}\n"
            context += f"Subdirectories: {', '.join(self.project_structure[rel_path]['dirs'])}\n"
        
        analysis = self._analyze_file_content(file_path)
        context += f"\nFile analysis: {analysis}\n"
        return context

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _get_ai_suggestion(self, file_path, content):
        context = self._get_context(file_path)
        file_type = self._categorize_file(file_path)
        prompt = f"""Analyze this file and suggest how to organize it within the project: {file_path}

File type: {file_type}
{context}

File content summary:
{content[:1000]}

Important: Consider the following guidelines when making suggestions:
1. Maintain the integrity of the project structure.
2. Do not break up files that import each other or have dependencies.
3. Keep related files in the same directory.
4. Suggest creating subdirectories only for logically separate components.
5. Rename files if it improves clarity, but maintain consistency.
6. Suggest deleting files only if they are clearly obsolete or redundant.
7. Add notes to files to explain their purpose or suggest improvements.
8. Consider the overall project architecture when making suggestions.
9. For non-text files, focus on organizing based on filename and file type.

Provide your suggestions using the available tools. You can use multiple tools if needed."""

        try:
            response = self.client.chat.completions.create(
                model=self.config.TEXT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                tools=self.config.TOOLS,
                max_tokens=500
            )
            return response
        except Exception as e:
            print(f"Error getting AI suggestion for {file_path}: {str(e)}")
            raise

    def _execute_suggestion(self, response, original_path):
        if response is None or not hasattr(response.choices[0].message, 'tool_calls'):
            print(f"No valid suggestions for {original_path}")
            return
        
        tool_calls = response.choices[0].message.tool_calls
        if not tool_calls:
            print(f"No tool calls in response for {original_path}")
            return

        for tool_call in tool_calls:
            function = tool_call.function
            tool_name = function.name
            try:
                args = json.loads(function.arguments)
            except json.JSONDecodeError:
                print(f"Invalid JSON in tool arguments for {original_path}")
                continue

            current_path = self.file_locations.get(original_path)
            if not current_path or not os.path.exists(current_path):
                print(f"File no longer exists or has been moved: {current_path}")
                return

            if tool_name == "move_file":
                destination = os.path.join(self.config.ROOT_PATH, args.get('destination'))
                if self._is_safe_to_move(current_path, destination):
                    if not os.path.isdir(current_path):
                        backup_path = self._create_backup(current_path)
                        if backup_path:
                            print(f"Created backup: {backup_path}")
                    new_path = move_file(current_path, destination)
                    if new_path:
                        self.changes.append(("move", current_path, new_path))
                        self.file_locations[original_path] = new_path
                        print(f"Updated file location: {original_path} -> {new_path}")
                else:
                    print(f"Unsafe to move file: {current_path}")
            elif tool_name == "create_folder":
                folder_path = os.path.join(self.config.ROOT_PATH, args.get('path'))
                create_folder(folder_path)
            elif tool_name == "add_note":
                success = add_note(current_path, args.get('note'))
                if not success:
                    print(f"Failed to add note to {current_path}")
            elif tool_name == "rename_file":
                new_name = args.get('new_name')
                if new_name:
                    if not os.path.isdir(current_path):
                        backup_path = self._create_backup(current_path)
                        if backup_path:
                            print(f"Created backup: {backup_path}")
                    new_path = rename_file(current_path, new_name)
                    if new_path:
                        self.changes.append(("rename", current_path, new_path))
                        self.file_locations[original_path] = new_path
                        print(f"Renamed file: {current_path} -> {new_path}")
            elif tool_name == "delete_file":
                if not os.path.isdir(current_path):
                    backup_path = self._create_backup(current_path)
                    if backup_path:
                        print(f"Created backup: {backup_path}")
                if delete_file(current_path):
                    self.changes.append(("delete", current_path, None))
                    del self.file_locations[original_path]
                    print(f"Deleted file: {current_path}")

    def _is_safe_to_move(self, source, destination):
        source_dir = os.path.dirname(source)
        dest_dir = os.path.dirname(destination)
        
        # Check if the file has dependencies
        if source in self.dependencies:
            # If moving to a different directory, check if it breaks dependencies
            if source_dir != dest_dir:
                for dep_file, deps in self.dependencies.items():
                    if os.path.basename(source) in deps and os.path.dirname(dep_file) == source_dir:
                        return False
        
        return True

    def undo_changes(self):
        for change in reversed(self.changes):
            action, source, destination = change
            if action == "move" or action == "rename":
                if os.path.exists(destination) and not os.path.exists(source):
                    try:
                        shutil.move(destination, source)
                        print(f"Undid {action}: {destination} -> {source}")
                        for original, current in self.file_locations.items():
                            if current == destination:
                                self.file_locations[original] = source
                                break
                    except Exception as e:
                        print(f"Error undoing {action} {destination} -> {source}: {str(e)}")
                else:
                    print(f"Cannot undo {action}: {destination} -> {source}")
            elif action == "delete":
                print(f"Cannot undo delete action for: {source}")
        self.changes.clear()

    def _generate_report(self):
        report = {
            "total_files_processed": len(self.file_locations),
            "changes_made": len(self.changes),
            "file_categories": {},
            "actions_taken": {
                "move": 0,
                "rename": 0,
                "delete": 0,
                "add_note": 0,
                "create_folder": 0
            }
        }

        for change in self.changes:
            action = change[0]
            report["actions_taken"][action] += 1

        for file_path in self.file_locations.values():
            category = self._categorize_file(file_path)
            report["file_categories"][category] = report["file_categories"].get(category, 0) + 1

        return report

    def organize_folder(self, folder_path, callback=None):
        self.config.ROOT_PATH = folder_path
        self._analyze_dependencies(folder_path)
        self._build_project_structure(folder_path)
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                original_path = os.path.join(root, file)
                self.file_locations[original_path] = original_path
                self._process_file(original_path, callback)

    def _analyze_dependencies(self, folder_path):
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self.dependencies[file_path] = self._get_file_dependencies(file_path)

    def _get_file_dependencies(self, file_path):
        dependencies = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                import_lines = re.findall(r'^(?:from|import)\s+(\w+)', content, re.MULTILINE)
                dependencies.update(import_lines)
        except Exception as e:
            print(f"Error parsing dependencies in {file_path}: {str(e)}")
        return list(dependencies)

    def _build_project_structure(self, folder_path):
        for root, dirs, files in os.walk(folder_path):
            rel_path = os.path.relpath(root, folder_path)
            self.project_structure[rel_path] = {
                'dirs': dirs,
                'files': files
            }
import os
import shutil

def move_file(source, destination):
    try:
        if not os.path.exists(source):
            print(f"Source file does not exist: {source}")
            return None
        
        abs_destination = os.path.abspath(destination)
        dest_dir = os.path.dirname(abs_destination)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        
        shutil.move(source, abs_destination)
        print(f"Successfully moved file from {source} to {abs_destination}")
        return abs_destination
    except PermissionError:
        print(f"Permission denied when moving file from {source} to {destination}")
        return None
    except Exception as e:
        print(f"Error moving file from {source} to {destination}: {str(e)}")
        return None

def create_folder(path):
    try:
        os.makedirs(path, exist_ok=True)
        print(f"Successfully created folder: {path}")
    except PermissionError:
        print(f"Permission denied when creating folder: {path}")
    except Exception as e:
        print(f"Error creating folder {path}: {str(e)}")

def add_note(file_path, note):
    try:
        if not os.path.exists(file_path):
            print(f"File does not exist: {file_path}")
            return False
        
        if os.path.isdir(file_path):
            print(f"Cannot add note to a directory: {file_path}")
            return False
        
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(f"\n\n# AI Note: {note}")
        print(f"Successfully added note to file: {file_path}")
        return True
    except PermissionError:
        print(f"Permission denied when adding note to file: {file_path}")
        return False
    except Exception as e:
        print(f"Error adding note to file {file_path}: {str(e)}")
        return False

def rename_file(source, new_name):
    try:
        new_path = os.path.join(os.path.dirname(source), new_name)
        os.rename(source, new_path)
        print(f"Successfully renamed file from {source} to {new_path}")
        return new_path
    except Exception as e:
        print(f"Error renaming file {source}: {str(e)}")
        return None

def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"Successfully deleted file: {file_path}")
        return True
    except Exception as e:
        print(f"Error deleting file {file_path}: {str(e)}")
        return False
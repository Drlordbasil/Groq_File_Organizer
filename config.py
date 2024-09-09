import os

class Config:
    def __init__(self):
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        self.TEXT_MODEL = "llama-3.1-70b-versatile"
        self.VISION_MODEL = "llava-v1.5-7b-4096-preview"
        self.ROOT_PATH = ""  # Set this when initializing the FileOrganizer
        self.TOOLS = [
            {
                "type": "function",
                "function": {
                    "name": "move_file",
                    "description": "Move a file to a new location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string"},
                            "destination": {"type": "string"}
                        },
                        "required": ["source", "destination"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_folder",
                    "description": "Create a new folder",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_note",
                    "description": "Add a note to a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"},
                            "note": {"type": "string"}
                        },
                        "required": ["file_path", "note"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "rename_file",
                    "description": "Rename a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string"},
                            "new_name": {"type": "string"}
                        },
                        "required": ["source", "new_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_file",
                    "description": "Delete a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"}
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_tag",
                    "description": "Add a tag to a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"},
                            "tag": {"type": "string"}
                        },
                        "required": ["file_path", "tag"]
                    }
                }
            }
        ]
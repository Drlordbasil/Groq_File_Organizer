# AI File Organizer

AI File Organizer is a Python-based application that uses artificial intelligence to help organize your files and folders. It analyzes the content and structure of your files and suggests ways to organize them more effectively.

## Features

- Intelligent file analysis and organization suggestions
- Supports various file types including text, code, documents, and archives
- Detects and handles file dependencies
- Creates backups before making changes
- Provides undo functionality for all changes
- User-friendly GUI for easy interaction

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Drlordbasil/Groq_File_Organizer.git
   cd groq_file_organizer
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your Groq API key:
   - Sign up for a Groq account and obtain an API key
   - Set the API key as an environment variable:
     ```bash
     export GROQ_API_KEY=your_api_key_here
     ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. Use the GUI to select a folder for organization.

3. Click "Organize Files" to start the process.

4. Review the suggested changes in the log.

5. Use the "Undo Changes" button if needed.

## How It Works

1. The application scans the selected folder and analyzes each file.
2. It uses the Groq API to generate intelligent suggestions for file organization.
3. The suggestions are executed, moving, renaming, or adding notes to files as needed.
4. A "delete_these" folder is created for files suggested for deletion, allowing for user review.
5. All changes are logged and can be undone if necessary.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
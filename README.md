# AI Living Documentation Engine

An intelligent documentation system that automatically analyzes Git changes and generates comprehensive documentation using AI. Built with FastAPI and OpenAI's GPT-4.

## 🚀 Features

- **Automated Documentation Generation**: Analyzes Git repository changes and creates detailed documentation
- **AI-Powered Analysis**: Uses GPT-4 to understand code changes and their impact
- **Markdown File Management**: Reads, writes, and edits markdown documentation files
- **Git Integration**: Monitors repository status and diff changes
- **Command Execution**: Runs shell commands for extended functionality
- **RESTful API**: Simple FastAPI-based interface for triggering documentation generation

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python)
- **AI**: OpenAI GPT-4
- **Language**: Python 3.14
- **Documentation**: Markdown files
- **Version Control**: Git

## 📋 Prerequisites

- Python 3.14+
- OpenAI API key
- Git repository

## 🔧 Installation

1. **Clone the repository:**

```bash
git clone <your-repo-url>
cd SC_AI_DOCS
```

2. **Create and activate virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
   Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

## 🚀 Usage

1. **Start the server:**

```bash
uvicorn app:app --reload
```

2. **Access the API:**

- API Documentation: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

3. **Generate Documentation:**

```bash
curl http://localhost:8000/generate_api_overview
```

## 📖 API Endpoints

### `GET /generate_api_overview`
- Triggers the AI documentation workflow: analyzes git status & diffs, reads markdown files, generates documentation, and updates files accordingly.

**Sample Response:**
```json
{
  "content": "Documentation generation completed successfully"
}
```

### Helper Tool Endpoints
You can use the following internal tools programmatically (direct calls may require API wrapper extensions):

- `check_git_status()` – Returns current git status and diff
- `run_command(cmd: str)` – Runs a shell command and returns output, error, and exit code
- `read_md_file(filename: str)` – Reads a markdown file’s content
- `write_md_file(input_str: str)` – Creates/overwrites a markdown file; input is `filename.md|content`
- `edit_md_file(input_str: str)` – Edits markdown file in place; input is `filename.md|old_content|new_content`
- `list_md_files(data: str = "")` – Lists all markdown files in the project directory
- `add(a, b)`, `subtract(a, b)`, `multiply(a, b)` – Arithmetic helpers, primarily for demonstration/agent reasoning purposes

## 🗂️ Project Structure

```
SC_AI_DOCS/
├── app.py                # Main FastAPI application and tool implementations
├── requirements.txt      # Python dependencies
├── api_overview.md       # API overview documentation (generated)
├── change_summary_*.md   # Generated change summaries (AI output)
├── venv/                 # Virtual environment
└── README.md             # Project documentation
```

## 🤖 Architecture & Workflow

The AI agent follows a strict, iterative workflow inspired by the "plan, action, observe, write, output" loop:

1. **Plan**: Analyze information needed and next steps
2. **Action**: Call available tools (git status, file readers, etc)
3. **Observe**: Process tool results & adjust plan
4. **Write**: Generate and save updated documentation (e.g., editing README.md)
5. **Output**: Provide completion summary

### How the AI Documentation Loop Works
- The agent works using messages and JSON instructions, with steps strictly logged as JSON.
- Tool output and agent actions are all governed by JSON-formatted responses.
- Designed for extensibility: New tools or workflows can be added easily by extending FastAPI endpoints and tool dictionary.

## 📝 Documentation Output

AI-generated documentation typically includes:
- **Summary**: Overview of changes
- **Files Changed**: List of modified files
- **Key Changes**: Detailed change descriptions
- **Impact**: How changes affect the system
- **Breaking Changes**: Any critical or backward-incompatible updates

## 🔒 Environment Variables

| Variable         | Description         | Required |
| ---------------- | ------------------- | -------- |
| `OPENAI_API_KEY` | Your OpenAI API key | Yes      |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Local Development Tips**
- Ensure you run the app in a clean virtual environment before submitting PRs
- Validate endpoints using the provided Swagger docs at `/docs`
- Add/update requirements.txt as needed for new dependencies

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋 Support

If you have questions or need help:
- Open an issue on GitHub
- Review API documentation at `/docs`

---

**Made with ❤️ and AI**

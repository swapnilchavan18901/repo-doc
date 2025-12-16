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

## 📚 API Endpoints

### GET `/generate_api_overview`

Triggers the AI documentation generation process that:

- Analyzes current Git status and changes
- Reads existing markdown documentation
- Generates comprehensive change summaries
- Updates or creates documentation files

**Response:**

```json
{
  "content": "Documentation generation completed successfully"
}
```

## 📁 Project Structure

```
SC_AI_DOCS/
├── app.py                 # Main FastAPI application
├── requirements.txt       # Python dependencies
├── api_overview.md       # API overview documentation
├── change_summary_*.md   # Generated change summaries
├── venv/                 # Virtual environment
└── README.md            # Project documentation
```

## 🤖 How It Works

The AI agent follows a structured workflow:

1. **Plan**: Analyzes what information is needed
2. **Action**: Calls tools to gather data (Git status, file reading, etc.)
3. **Observe**: Processes tool results
4. **Write**: Generates and saves documentation
5. **Output**: Provides completion summary

### Available Tools:

- `check_git_status()` - Gets Git status and diff
- `run_command()` - Executes shell commands
- `read_md_file()` - Reads markdown files
- `write_md_file()` - Creates/overwrites markdown files
- `edit_md_file()` - Edits existing markdown files
- `list_md_files()` - Lists all markdown files

## 📝 Documentation Output

Generated documentation includes:

- **Summary**: Overview of changes
- **Files Changed**: List of modified files
- **Key Changes**: Detailed change descriptions
- **Impact**: How changes affect the system
- **Breaking Changes**: Any breaking modifications

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

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋 Support

If you have any questions or need help:

- Open an issue on GitHub
- Check the API documentation at `/docs`

---

**Made with ❤️ and AI**

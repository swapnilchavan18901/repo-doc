# Project Feature Documentation

## Project Overview
This project is a FastAPI-based API platform that showcases best practices for API design, synchronous and asynchronous route handling, external service integration, and automated developer documentation tooling. The platform includes demo endpoints, integration with GitHub's API, robust markdown editing tools, and utility functions for developer productivity (shell commands, git status reporting, and more).

Key technologies: **FastAPI**, **aiohttp**, **requests**, **Pydantic**, **OpenAI API**, **dotenv**, **Markdown**.

---

## Feature Catalog
### 1. API Endpoints & Routing
- Modular routing using FastAPI routers, providing clean separation between demo, base, and example APIs.
- Support for both sync and async endpoint handlers for maximum flexibility and performance.

### 2. Hello World Endpoint
- **Endpoint:** `GET /api/example`
- Returns a friendly greeting: `{"payload": "Hello {name or world}!"}`
- Optional `name` query parameter to personalize the message.

### 3. GitHub User Info (Sync & Async)
- **Endpoints:**
    - `GET /api/example/github` (sync)
    - `GET /api/example/github/async` (async)
- Fetches information about the authenticated GitHub user via the GitHub API.
- Returns username, follower count, and public repo count as JSON.

### 4. Markdown File Management & Developer Utilities
- Programmatic utilities for:
    - Reading, writing, and editing markdown documentation files.
    - Executing shell commands with output/error reporting.
    - Checking git status and git diff.
- CLI and web integration with these tools for streamlined developer UX.

### 5. Dynamic API & Documentation Generation
- Automated documentation workflow via code (`generate_feature_docs.py`).
- Dynamic OpenAI-based generation of project documentation.


---

## Quick Start

1. **Clone the repository**
```sh
git clone <your_repo_url>
cd <your_repo>
```
2. **Install requirements**
```sh
pip install -r requirements.txt
```
3. **Setup environment variables**
Create a `.env` file with the following variables:
```
OPENAI_API_KEY=your_openai_api_key
github_token=your_github_pat
```
4. **Run the FastAPI application**
```sh
uvicorn app:app --reload
```
- Access base API at: http://localhost:8000/
- Demo API: http://localhost:8000/api/example
- API docs (Swagger UI): http://localhost:8000/docs

---

## API Reference

### 1. Demo and Example Routes

#### `GET /api/example`
- **Description:** Returns a hello world message or personalized greeting if `name` is provided.
- **Query Parameters:**
    - `name` (optional, string): Name to greet.
- **Response:**
```json
{
  "payload": "Hello {name or world}!"
}
```

#### `GET /api/example/github`
- **Description:** Fetch details of authorized GitHub user synchronously.
- **Response Model:**
```json
{
  "user_name": "<username>",
  "followers": 42,
  "repo_count": 10
}
```

#### `GET /api/example/github/async`
- **Description:** Fetch details of authorized GitHub user asynchronously (uses `aiohttp`).
- **Response:** _Same as above._

### 2. Internal Utilities (available as Python functions, not HTTP endpoints)
- **add(a: int, b: int):** Return sum
- **subtract(a: int, b: int):** Return difference
- **multiply(a: int, b: int):** Return product
- **run_command(cmd: str):** Execute shell command and get output/return code
- **check_git_status():** Get `git status` and `git diff`
- **read_md_file(filename: str):** Get content of a markdown file
- **write_md_file('filename.md|content'):** Write/overwrite markdown file
- **edit_md_file('filename.md|old_content|new_content'):** Replace content in markdown file

---

## Configuration

| Variable            | Description                                   |
|---------------------|-----------------------------------------------|
| OPENAI_API_KEY      | API key for OpenAI API (required for doc tools)|
| github_token        | GitHub personal access token (for user info)  |

- Place these in your `.env` file at the project root.

---

## Examples

**Fetching a personalized hello:**
```sh
curl 'http://localhost:8000/api/example?name=Sam'
# Response: { "payload": "Hello Sam!" }
```

**Fetching GitHub user info (sync):**
```sh
curl 'http://localhost:8000/api/example/github'
# Response: { "user_name": "octocat", "followers": 3000, "repo_count": 7 }
```

**Write markdown file via utility:**
```python
from app import write_md_file
write_md_file('test.md|# My Title\nSome content')
```

**Run a shell command:**
```python
from app import run_command
run_command('ls -la')
```

---

## Contributing

1. Fork & clone the repo
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set your keys
4. Use feature branches for PRs
5. Run all code and lint before pushing
6. Detailed documentation must be placed in `FEATUREREADME.md` – not `README.md`
7. Use `generate_feature_docs.py` to update documentation on major feature changes

---

## Best Practices
- Only store secrets in `.env` (never commit real keys)
- Use async endpoints for network-bound operations
- Keep documentation feature-focused: update `FEATUREREADME.md` with each new API or capability
- Place all new endpoints inside module routers (not directly in app.py)

---

For more information and latest developer tools, see `/generate_api_overview` endpoint or run the documentation utilities.

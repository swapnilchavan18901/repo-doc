# Project Feature Documentation

## Project Overview

This project is a FastAPI-based API platform that showcases best practices for API design, synchronous and asynchronous route handling, external service integration, and automated developer documentation tooling. The platform includes demo endpoints, integration with GitHub's API, robust markdown editing tools, and utility functions for developer productivity (shell commands, git status reporting, and more).

Key technologies: **FastAPI**, **aiohttp**, **requests**, **Pydantic**, **OpenAI API**, **dotenv**, **Markdown**.

---

## Feature Catalog

### 1. API Endpoints & Routing

- Modular routing using FastAPI routers, providing clean separation between demo, base, and example APIs.
- Support for both sync and async endpoint handlers for maximum flexibility and performance.
- **NEW:** Dedicated route for `/dinkachika/` providing a basic "Hello, World!" example for health checks or minimal responses.

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

- Comprehensive utilities for markdown/documentation workflows:
  - **Reading, writing, and editing markdown files programmatically**
  - **Ultra-efficient line-based editing** – Only the specified line range is changed (`edit_md_file('filename.md|start_line|end_line|new_content')`), ideal for precise, large-document updates.
  - Classic content-based editing (`edit_md_file('filename.md|old_content|new_content')`) as a fallback, but line-based editing is now preferred for all updates.
  - Automatic line number retrieval using `read_md_file`, which returns content with line numbers for easy targeting.
- **Secure Shell Command Execution & Validation:**
  - The `run_command(cmd: str)` utility executes shell commands, but only allows a strict set of read-only or diagnostic commands (such as `ls`, `cat`, `head`, `git status`, etc.) which match a project-managed **whitelist** of regular expressions for safety.
### 5. Dynamic API & Documentation Generation

- Automated documentation workflow via code (`generate_feature_docs.py`).
- Dynamic OpenAI-based generation of project documentation with strict agent loop safety.
- **AI Agent Max Iterations (runaway guard):** All AI-driven doc generation runs are protected by a `max_iterations` parameter (default: 50), ensuring the main agent loop cannot execute unchecked. If the agent hits this limit, a warning is returned and the loop stops automatically—make sure to increase max_iterations only for large doc updates.
- To customize the loop limit, pass `generate_feature_docs(max_iterations=NN)` when invoking from Python. This helps protect against runaway API costs and accidental infinite loops.

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
- Dinkachika endpoint: http://localhost:8000/dinkachika/
- API docs (Swagger UI): http://localhost:8000/docs

---

## API Reference

### 1. Dinkachika Route

#### `GET /dinkachika/`
- **Description:** Returns a plain text response 'Hello, World!'. Useful for health checks, basic testing, or as a minimal demo endpoint.
- **Response:**

```
Hello, World!
```

### 2. Demo and Example Routes

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

### 3. Internal Utilities (available as Python functions, not HTTP endpoints)

- **add(a: int, b: int):** Return sum
- **subtract(a: int, b: int):** Return difference
- **multiply(a: int, b: int):** Return product
- **run_command(cmd: str):** Execute shell command and get output/return code
- **check_git_status():** Get `git status` and `git diff`
- **read_md_file(filename: str):** Returns content of a markdown file with line numbers (`LINE | CONTENT`), ideal for identifying ranges for editing.
- **write_md_file('filename.md|content'):** Write/overwrite markdown file in one call.
- **edit_md_file (preferred line-based editing):**
    - `'filename.md|start_line|end_line|new_content'`: Replace specific line range (1-based, inclusive)
    - Example: `edit_md_file('FEATUREREADME.md|90|110|New feature content here...')` (replaces lines 90-110)
- **edit_md_file (legacy content-based editing):**
    - `'filename.md|old_content|new_content'`: Replaces first occurrence of old_content in the file.
    - Less efficient; only use if precise line numbers are unknown.

---

## Configuration

| Variable       | Description                                     |
| -------------- | ----------------------------------------------- |
| OPENAI_API_KEY | API key for OpenAI API (required for doc tools) |
| github_token   | GitHub personal access token (for user info)    |

- Place these in your `.env` file at the project root.

---

## Examples

**Calling the Dinkachika endpoint:**

```sh
curl http://localhost:8000/dinkachika/
# Response: Hello, World!
```

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

**Efficient line-based editing (preferred):**

```python
from app import edit_md_file
# Replace lines 5-7 in FEATUREREADME.md with new content
edit_md_file('FEATUREREADME.md|5|7|# Updated title\nNew overview here...')
```

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

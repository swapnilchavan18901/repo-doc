import requests
import base64
import jwt
import time
from typing import Dict, List, Any, Optional
from env import GITHUB_APP_ID, GITHUB_PRIVATE_KEY


class GitHubService:
    """
    GitHub API service for accessing repository data.
    Provides methods to get diffs, read files, and explore repo structure.
    """
    def __init__(self):
        """
        Initialize GitHub service.
        Thread-safe: No instance state for repo_full_name.
        """
        self.app_id = GITHUB_APP_ID
        self.private_key = GITHUB_PRIVATE_KEY
        self.base_url = "https://api.github.com"
        self.installation_token = None
        self.token_expires_at = 0
    
    def _generate_jwt(self) -> str:
        """Generate JWT for GitHub App authentication"""
        now = int(time.time())
        
        
        payload = {
            "iat": now - 60,  # Issued 60 seconds in the past to account for clock drift
            "exp": now + (10 * 60),  # Expires in 10 minutes
            "iss": self.app_id
        }
        return jwt.encode(payload, self.private_key, algorithm="RS256")
    
    def _get_installation_token(self, repo_full_name: str) -> str:
        """Get installation access token for a repository"""
        # Check if we have a valid cached token
        if self.installation_token and time.time() < self.token_expires_at:
            return self.installation_token
        
        # Generate JWT for authentication
        jwt_token = self._generate_jwt()
        
        # Get installation ID for the repository
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        # First, get the installation ID
        owner, repo = repo_full_name.split('/')
        install_url = f"{self.base_url}/repos/{repo_full_name}/installation"
        
        try:
            res = requests.get(install_url, headers=headers)
            if res.status_code != 200:
                raise Exception(f"Failed to get installation: {res.text}")
            
            installation_id = res.json()["id"]
            
            # Exchange JWT for installation token
            token_url = f"{self.base_url}/app/installations/{installation_id}/access_tokens"
            res = requests.post(token_url, headers=headers)
            
            if res.status_code != 201:
                raise Exception(f"Failed to get installation token: {res.text}")
            
            token_data = res.json()
            self.installation_token = token_data["token"]
            # Cache token (expires in 1 hour, refresh 5 min early)
            self.token_expires_at = time.time() + (55 * 60)
            
            return self.installation_token
            
        except Exception as e:
            raise Exception(f"GitHub App authentication failed: {str(e)}")
    
    def _get_headers(self, repo_full_name: str) -> Dict[str, str]:
        """Get authenticated headers for API requests"""
        token = self._get_installation_token(repo_full_name)
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def get_diff(self, input_str: str) -> Dict[str, Any]:
        """
        Get the diff between two commits using GitHub Compare API.
        Format: 'repo_full_name|before_sha|after_sha'
        
        Args:
            input_str: Pipe-delimited string 'repo_full_name|before_sha|after_sha'
            
        Returns:
            Dictionary with success status and diff data
        """
        try:
            if input_str.count('|') != 2:
                return {"success": False, "error": "Input must be in format 'repo_full_name|before_sha|after_sha'"}
            
            repo_full_name, before_sha, after_sha = input_str.split('|')
            repo_full_name = repo_full_name.strip()
            before_sha = before_sha.strip()
            after_sha = after_sha.strip()
        except Exception as e:
            return {"success": False, "error": f"Failed to parse input: {str(e)}", "input": input_str}
        
        url = f"{self.base_url}/repos/{repo_full_name}/compare/{before_sha}...{after_sha}"
        
        try:
            headers = self._get_headers(repo_full_name)
            res = requests.get(url, headers=headers)
            
            if res.status_code != 200:
                return {
                    "success": False,
                    "error": f"GitHub API error: {res.status_code}",
                    "details": res.text
                }
            
            data = res.json()
            
            # Extract file changes and diffs
            files_changed = []
            for file in data.get("files", []):
                files_changed.append({
                    "filename": file["filename"],
                    "status": file["status"],  # added, modified, removed, renamed
                    "additions": file["additions"],
                    "deletions": file["deletions"],
                    "changes": file["changes"],
                    "patch": file.get("patch", ""),  # Actual diff content
                })
            
            return {
                "success": True,
                "total_commits": len(data.get("commits", [])),
                "files_changed": files_changed,
                "total_files": len(files_changed),
                "ahead_by": data.get("ahead_by", 0),
                "behind_by": data.get("behind_by", 0),
                "compare_url": data.get("html_url", "")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_file_tree(self, input_str: str) -> Dict[str, Any]:
        """
        Get the file tree/directory structure of the repository.
        Format: 'repo_full_name|sha|path' (path optional)
        
        Args:
            input_str: Pipe-delimited string 'repo_full_name|sha|path' (path optional)
            
        Returns:
            Dictionary with success status and file tree
        """
        try:
            parts = input_str.split('|')
            if len(parts) < 2:
                return {"success": False, "error": "Input must be in format 'repo_full_name|sha|path' (path optional)"}
            
            repo_full_name = parts[0].strip()
            sha = parts[1].strip()
            path = parts[2].strip() if len(parts) > 2 else ""
        except Exception as e:
            return {"success": False, "error": f"Failed to parse input: {str(e)}", "input": input_str}
        
        url = f"{self.base_url}/repos/{repo_full_name}/contents/{path}?ref={sha}"
        
        try:
            headers = self._get_headers(repo_full_name)
            res = requests.get(url, headers=headers)
            
            if res.status_code != 200:
                return {
                    "success": False,
                    "error": f"GitHub API error: {res.status_code}",
                    "details": res.text
                }
            
            data = res.json()
            
            # Parse directory contents
            contents = []
            for item in data:
                contents.append({
                    "name": item["name"],
                    "path": item["path"],
                    "type": item["type"],  # file or dir
                    "size": item.get("size", 0),
                    "sha": item["sha"],
                    "url": item.get("html_url", "")
                })
            
            return {
                "success": True,
                "path": path if path else "/",
                "items": contents,
                "count": len(contents)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def read_file(self, input_str: str) -> Dict[str, Any]:
        """
        Read the content of a specific file from GitHub.
        Format: 'repo_full_name|filepath|sha' (sha optional, defaults to main)
        
        Args:
            input_str: Pipe-delimited string 'repo_full_name|filepath|sha' (sha optional)
            
        Returns:
            Dictionary with success status and file content
        """
        try:
            parts = input_str.split('|')
            if len(parts) < 2:
                return {"success": False, "error": "Input must be in format 'repo_full_name|filepath|sha' (sha optional)"}
            
            repo_full_name = parts[0].strip()
            filepath = parts[1].strip()
            sha = parts[2].strip() if len(parts) > 2 else "main"
        except Exception as e:
            return {"success": False, "error": f"Failed to parse input: {str(e)}", "input": input_str}
        
        url = f"{self.base_url}/repos/{repo_full_name}/contents/{filepath}?ref={sha}"
        
        try:
            headers = self._get_headers(repo_full_name)
            res = requests.get(url, headers=headers)
            
            if res.status_code != 200:
                return {
                    "success": False,
                    "error": f"GitHub API error: {res.status_code}",
                    "details": res.text,
                    "filepath": filepath
                }
            
            data = res.json()
            
            # GitHub returns content as base64 encoded
            if data.get("encoding") == "base64":
                content = base64.b64decode(data["content"]).decode("utf-8")
            else:
                content = data.get("content", "")
            
            return {
                "success": True,
                "filepath": filepath,
                "content": content,
                "size": data.get("size", 0),
                "sha": data["sha"]
            }
            
        except UnicodeDecodeError:
            return {
                "success": False,
                "error": "File is not text-readable (binary file)",
                "filepath": filepath
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "filepath": filepath
            }

    def search_code(self, input_str: str) -> Dict[str, Any]:
        """
        Search for code in the repository.
        Format: 'repo_full_name|query|max_results' (max_results optional)
        
        Args:
            input_str: Pipe-delimited string 'repo_full_name|query|max_results' (max_results optional)
            
        Returns:
            Dictionary with success status and search results
        """
        try:
            parts = input_str.split('|')
            if len(parts) < 2:
                return {"success": False, "error": "Input must be in format 'repo_full_name|query|max_results' (max_results optional)"}
            
            repo_full_name = parts[0].strip()
            query = parts[1].strip()
            max_results = int(parts[2].strip()) if len(parts) > 2 else 10
        except ValueError:
            return {"success": False, "error": "max_results must be an integer", "input": input_str}
        except Exception as e:
            return {"success": False, "error": f"Failed to parse input: {str(e)}", "input": input_str}
        
        # Build search query with repo scope
        search_query = f"{query} repo:{repo_full_name}"
        url = f"{self.base_url}/search/code"
        params = {
            "q": search_query,
            "per_page": min(max_results, 100)  # GitHub max is 100
        }
        
        try:
            headers = self._get_headers(repo_full_name)
            res = requests.get(url, headers=headers, params=params)
            
            if res.status_code != 200:
                return {
                    "success": False,
                    "error": f"GitHub API error: {res.status_code}",
                    "details": res.text
                }
            
            data = res.json()
            
            # Parse search results
            results = []
            for item in data.get("items", []):
                results.append({
                    "name": item["name"],
                    "path": item["path"],
                    "sha": item["sha"],
                    "url": item.get("html_url", ""),
                    "repository": item["repository"]["full_name"]
                })
            
            return {
                "success": True,
                "query": query,
                "total_count": data.get("total_count", 0),
                "results": results,
                "result_count": len(results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_commit_info(self, input_str: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific commit.
        Format: 'repo_full_name|commit_sha'
        
        Args:
            input_str: Pipe-delimited string 'repo_full_name|commit_sha'
            
        Returns:
            Dictionary with success status and commit info
        """
        try:
            if input_str.count('|') != 1:
                return {"success": False, "error": "Input must be in format 'repo_full_name|commit_sha'"}
            
            repo_full_name, commit_sha = input_str.split('|')
            repo_full_name = repo_full_name.strip()
            commit_sha = commit_sha.strip()
        except Exception as e:
            return {"success": False, "error": f"Failed to parse input: {str(e)}", "input": input_str}
        
        url = f"{self.base_url}/repos/{repo_full_name}/commits/{commit_sha}"
        
        try:
            headers = self._get_headers(repo_full_name)
            res = requests.get(url, headers=headers)
            
            if res.status_code != 200:
                return {
                    "success": False,
                    "error": f"GitHub API error: {res.status_code}",
                    "details": res.text
                }
            
            data = res.json()
            
            return {
                "success": True,
                "sha": data["sha"],
                "message": data["commit"]["message"],
                "author": data["commit"]["author"]["name"],
                "date": data["commit"]["author"]["date"],
                "files_changed": len(data.get("files", [])),
                "additions": data["stats"]["additions"],
                "deletions": data["stats"]["deletions"],
                "total_changes": data["stats"]["total"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def list_all_files_recursive(self, input_str: str) -> Dict[str, Any]:
        """
        Recursively list all files in the repository (not just top level).
        Format: 'repo_full_name|sha|path' (sha and path optional)
        
        Args:
            input_str: Pipe-delimited string 'repo_full_name|sha|path' (sha and path optional)
            
        Returns:
            Dictionary with success status and flat list of all files
        """
        try:
            parts = input_str.split('|')
            if len(parts) < 1:
                return {"success": False, "error": "Input must be in format 'repo_full_name|sha|path' (sha and path optional)"}
            
            repo_full_name = parts[0].strip()
            sha = parts[1].strip() if len(parts) > 1 else "main"
            path = parts[2].strip() if len(parts) > 2 else ""
        except Exception as e:
            return {"success": False, "error": f"Failed to parse input: {str(e)}", "input": input_str}
        
        all_files = []
        
        def traverse(current_path: str):
            tree_input = f"{repo_full_name}|{sha}|{current_path}"
            result = self.get_file_tree(tree_input)
            if not result["success"]:
                return
            
            for item in result["items"]:
                if item["type"] == "file":
                    all_files.append({
                        "path": item["path"],
                        "name": item["name"],
                        "size": item["size"]
                    })
                elif item["type"] == "dir":
                    traverse(item["path"])
        
        try:
            traverse(path)
            return {
                "success": True,
                "total_files": len(all_files),
                "files": all_files
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "partial_files": all_files
            }

from fastapi import FastAPI

app = FastAPI(title="AI Living Documentation Engine")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/read_file")
def read_file():
    with open("api_overview.md", "r") as file:
        content = file.read()
    return {"content": content}

    

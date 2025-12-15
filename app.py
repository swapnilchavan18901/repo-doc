from fastapi import FastAPI

app = FastAPI(title="AI Living Documentation Engine")

@app.get("/health")
def health():
    return {"status": "ok"}

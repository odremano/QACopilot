from fastapi import FastAPI

app = FastAPI(title="QA Copilot API", version="0.1.0")


@app.get("/salud")
def salud() -> dict:
    return {"estado": "ok"}

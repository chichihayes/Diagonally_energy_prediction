from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

load_dotenv()

from src.api.routes import router

app = FastAPI(title="Diagonally Energy Prediction")
app.include_router(router)
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")


@app.get("/health")
def health():
    return {"status": "ok"}

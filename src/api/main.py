from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

load_dotenv()

from src.api.routes import router
from src.services.scheduler import submit_smart_home_reading

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(submit_smart_home_reading, "interval", minutes=15)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Diagonally Energy Prediction", lifespan=lifespan)
app.include_router(router)
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")


@app.get("/health")
def health():
    return {"status": "ok"}

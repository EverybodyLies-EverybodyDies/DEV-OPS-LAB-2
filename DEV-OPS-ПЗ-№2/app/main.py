
import os
import logging
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

app = FastAPI(
    title="Task Management API",
    description="REST API deployed with Docker and Kubernetes",
    version="1.0.0"
)

LOG_DIR = Path("/shared")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_DIR / "app.log",
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ],
    force=True
)

logger = logging.getLogger("task-api")

tasks = {}
next_id = 1


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)

    logger.info(
        "%s %s - Status: %s",
        request.method,
        request.url.path,
        response.status_code
    )

    return response


@app.get("/")
def home():
    return {
        "message": "Task Management API is running",
        "status": "OK",
        "service": "FastAPI"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/tasks")
def get_tasks():
    return list(tasks.values())


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    return tasks[task_id]


@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    global next_id

    new_task = {
        "id": next_id,
        "title": task.title,
        "completed": False,
        "created_at": datetime.now().isoformat()
    }

    tasks[next_id] = new_task

    logger.info("Created task ID=%s", next_id)

    next_id += 1

    return new_task


@app.patch("/tasks/{task_id}")
def complete_task(task_id: int):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    tasks[task_id]["completed"] = not tasks[task_id]["completed"]

    logger.info("Updated task ID=%s", task_id)

    return tasks[task_id]


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    deleted = tasks.pop(task_id)

    logger.info("Deleted task ID=%s", task_id)

    return {
        "message": "Task deleted",
        "task": deleted
    }

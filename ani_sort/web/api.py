from typing import Union
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from ani_sort.db import init_db
from ani_sort.web.routes import tasks, works, config, gallery

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TASKS_FILE = BASE_DIR / "tasks" / "history.json"

app = FastAPI(title="AniSort WebUI", version="0.1")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.on_event("startup")
def startup_event():
    init_db()
    print("Database initialized")


app.include_router(tasks.router)
app.include_router(gallery.router)
# app.include_router(works.router)
# app.include_router(config.router)


@app.get("/")
def read_root():
    return {"Hello": "World"}


# def load_tasks():
#     if TASKS_FILE.exists():
#         with open(TASKS_FILE, "r", encoding="utf-8") as f:
#             return json.load(f)
#     return []


# @app.get("/", response_class=HTMLResponse)
# def index(request: Request):
#     tasks = load_tasks()[::-1]  # 最新在上
#     for t in tasks:
#         t["timestamp"] = datetime.fromisoformat(t["timestamp"]).strftime(
#             "%Y-%m-%d %H:%M:%S"
#         )
#     return templates.TemplateResponse(
#         "index.html", {"request": request, "tasks": tasks}
#     )


# @app.get("/tasks/{task_id}", response_class=HTMLResponse)
# def task_detail(request: Request, task_id: str):
#     tasks = load_tasks()
#     task = next((t for t in tasks if t["task_id"] == task_id), None)
#     if not task:
#         return HTMLResponse("<h3>Task not found</h3>", status_code=404)
#     return templates.TemplateResponse("detail.html", {"request": request, "task": task})

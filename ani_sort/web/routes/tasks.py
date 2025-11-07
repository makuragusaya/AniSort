import threading
from fastapi import APIRouter, Request, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ani_sort.db import SessionLocal, Task, WatchedFolder
from ani_sort.task import run_sort_task


router = APIRouter(tags=["Tasks"])
templates = Jinja2Templates(directory="ani_sort/web/templates")


@router.get("/", response_class=HTMLResponse)
def list_tasks(request: Request):
    db = SessionLocal()
    tasks = db.query(Task).order_by(Task.id.desc()).all()
    running_tasks = db.query(Task).filter(Task.status == "running").all()
    pending_tasks = (
        db.query(WatchedFolder).filter(WatchedFolder.status == "detected").all()
    )  # detected, processing, processed, removed
    return templates.TemplateResponse(
        "task.html",
        {
            "request": request,
            "tasks": tasks,
            "pending": pending_tasks,
            "running": running_tasks,
        },
    )


def long_sort_task(folder_path: str):
    print(f"Sorting started for {folder_path}")
    run_sort_task(input_path=folder_path)
    print(f"Sorting completed for {folder_path}")


@router.post("/run")
def run_task_from_web(background_tasks: BackgroundTasks, folder_id: int = Form(...)):
    db = SessionLocal()
    folder = db.query(WatchedFolder).filter_by(id=folder_id).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    background_tasks.add_task(long_sort_task, folder.path)

    return RedirectResponse("/", status_code=303)

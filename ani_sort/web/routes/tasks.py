from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ani_sort.db import SessionLocal, Task
from ani_sort.task import run_sort_task

router = APIRouter(prefix="/tasks", tags=["Tasks"])
templates = Jinja2Templates(directory="ani_sort/web/templates")


@router.get("/", response_class=HTMLResponse)
def list_tasks(request: Request):
    db = SessionLocal()
    tasks = db.query(Task).order_by(Task.id.desc()).all()
    pending_tasks = db.query(Task).filter(Task.status == "pending").all()
    return templates.TemplateResponse(
        "task.html", {"request": request, "tasks": tasks, "pending": pending_tasks}
    )


@router.post("/run")
def run_sort(input_path: str = Form(...), output_path: str = Form(None)):
    run_sort_task(
        input_path=input_path,
        output_dir=output_path if output_path else None,
    )
    return RedirectResponse(url="/tasks", status_code=303)

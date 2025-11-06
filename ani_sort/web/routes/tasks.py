from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ani_sort.db import SessionLocal, Task
from ani_sort.core import AniSort
from pathlib import Path

router = APIRouter(prefix="/tasks", tags=["Tasks"])
templates = Jinja2Templates(directory="ani_sort/web/templates")


@router.get("/", response_class=HTMLResponse)
def list_tasks(request: Request):
    db = SessionLocal()
    tasks = db.query(Task).order_by(Task.id.desc()).all()
    return templates.TemplateResponse(
        "task.html", {"request": request, "tasks": tasks}
    )


@router.post("/run")
def run_sort(input_path: str = Form(...), output_path: str = Form(None)):
    sorter = AniSort(Path(input_path), Path(output_path) if output_path else None)
    sorter.main()
    return RedirectResponse(url="/tasks", status_code=303)

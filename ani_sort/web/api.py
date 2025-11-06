from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from pathlib import Path
from ani_sort.db import init_db, SessionLocal, WatchedFolder
from ani_sort.web.routes import tasks, gallery
from ani_sort.config_manager import load_config
from ani_sort.watcher import start_watcher

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TASKS_FILE = BASE_DIR / "tasks" / "history.json"

app = FastAPI(title="AniSort WebUI", version="0.1")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def on_new_folder(folder_path, source):
    print(f"Detected new folder: {folder_path}")
    session = SessionLocal()
    task = WatchedFolder(path=str(folder_path), status="detected")
    session.add(task)
    session.commit()


@app.on_event("startup")
def startup_event():
    init_db()
    print("Database initialized")
    config = load_config()
    watch_path = Path(config.general.watch_folder)
    start_watcher(watch_path, on_new_folder)


app.include_router(tasks.router)
app.include_router(gallery.router)
# app.include_router(works.router)
# app.include_router(config.router)


@app.get("/")
def read_root():
    return {"Hello": "World"}

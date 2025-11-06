from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from ani_sort.db import SessionLocal, Anime
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/gallery", tags=["Gallery"])
templates = Jinja2Templates(directory="ani_sort/web/templates")


@router.get("/", response_class=HTMLResponse)
def anime_gallery(request: Request):
    session: Session = SessionLocal()
    animes = session.query(Anime).all()
    return templates.TemplateResponse(
        "gallery.html", {"request": request, "animes": animes}
    )



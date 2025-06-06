from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import services.jwt_service as jwt_manager
import routers.auth as auth_router
import routers.admin as admin_router
from sqlalchemy import create_engine

from models.user import Base
from config.db import SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth_router.router, prefix="")
app.include_router(admin_router.router, prefix="/admin")

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def mainPage(request: Request):
    tkn = request.cookies.get("session")
    data = {
            "request": request,
            "message": "Hello World!",
            }
    if jwt_manager.check_token(tkn):
        data.update({
            "user": {
                "username": jwt_manager.decode_access_token(tkn)["sub"],
                "is_admin": bool(jwt_manager.decode_access_token(tkn).get("is_admin", False))
            }
        })
    
    return templates.TemplateResponse("index.html", data)


@app.exception_handler(404)
async def not_found(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
@app.exception_handler(500)
async def internal_server_error(request: Request, exc):
    return templates.TemplateResponse("500.html", {"request": request}, status_code=500)
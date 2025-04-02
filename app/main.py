from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from app.api import auth, restaurant, views
from app.db.database import engine
from app.models import user, restaurant as restaurant_model

# Create database tables
user.Base.metadata.create_all(bind=engine)
restaurant_model.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your_session_secret_key")

app.include_router(auth.router)
app.include_router(restaurant.router)  # Optional API endpoints
app.include_router(views.router)

templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.core.config import settings
from app.core.logging import logger
from app.api import users


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(users.router)

@app.get("/")
def root():
    logger.info("Root endpoint called")
    return {"message": "Enterprise Document Management System API"}


@app.get("/health")
def health():
    return {"status": "healthy"}
from fastapi import FastAPI

from app.api.routes import api_router
from app.core.config import settings
from app.core.logging import logger


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
)

app.include_router(api_router)

@app.get("/")
def root():
    logger.info("Root endpoint called")
    return {"message": "Enterprise Document Management System API"}


@app.get("/health")
def health():
    return {"status": "healthy"}
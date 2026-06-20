from fastapi import FastAPI

app = FastAPI(
    title="Enterprise Document Management System",
    description="Backend APIs for enterprise document management",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "Enterprise Document Management System API",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
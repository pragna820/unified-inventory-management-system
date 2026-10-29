
from fastapi import FastAPI

app = FastAPI(
    title="Unified Inventory Management System",
    description="API for managing products and inventory",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Unified Inventory Management System API is running"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}

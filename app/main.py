# FastAPI Application
import logging
import time

from fastapi import FastAPI, HTTPException, Request
from app.database import Base, engine
from app.exception_handler import http_exception_handler
from app.routers.employee import router as employee_router
from app.routers import auth

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create Database Tables
Base.metadata.create_all(bind=engine)

logger.info("Database Tables Created Successfully")

# Create FastAPI Application
app = FastAPI(
    title="Employee Management API",
    version="1.0.0"
)

logger.info("Employee Management API Started")

# Register Router
app.include_router(employee_router)

app.include_router(auth.router)

# Register Global Exception Handler
app.add_exception_handler(
    HTTPException,
    http_exception_handler
)

# Middleware
@app.middleware("http")
async def log_requests(
    request: Request,
    call_next
):
    # Log incoming request
    logger.info(f"{request.method} {request.url.path}")

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logger.info(f"Completed in {process_time:.4f} seconds")

    response.headers["X-Process-Time"] = f"{process_time:.4f}"

    return response

# Root Endpoint

@app.get("/")
def root():
    logger.info("Root Endpoint Accessed")

    return {
        "message": "Employee Management API is Running"
    }
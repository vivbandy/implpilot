"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health

app = FastAPI(
    title="ImplPilot API",
    description="Project management and reporting for implementation teams",
    version="1.0.0",
)

# CORS configuration
# In production, restrict origins to your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ImplPilot API",
        "version": "1.0.0",
        "docs": "/docs",
    }

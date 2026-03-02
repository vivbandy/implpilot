"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, health, phases, projects

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
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(phases.router, prefix="/api/v1/phases", tags=["phases"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ImplPilot API",
        "version": "1.0.0",
        "docs": "/docs",
    }

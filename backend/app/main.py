from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .routes import admissions
from .config.database import db_connection
from rich.console import Console

console = Console()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the lifespan of the FastAPI application.
    Handles database connections setup and cleanup.
    """
    try:
        console.print("[yellow]Starting up InfoBurn API...[/yellow]")
        await db_connection.connect()
        console.print("[green]InfoBurn API startup complete![/green]")
        yield
    finally:
        console.print("[yellow]Shutting down InfoBurn API...[/yellow]")
        await db_connection.close()
        console.print("[green]InfoBurn API shutdown complete![/green]")

# Initialize FastAPI with enhanced metadata
app = FastAPI(
    title="InfoBurn API",
    description="""
    🏥 Burns Critical Care Unit Information System API
    
    This API provides endpoints for managing patient admissions and clinical data 
    in a burns critical care unit setting.
    
    ## Features
    * 📋 Patient admission data
    * 📊 Admission metrics
    * 📍 Burn data
    * 📝 Clinical data
    
    ## Authentication
    All endpoints require appropriate authentication credentials.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint providing API status and version information.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "operational",
            "service": "InfoBurn API",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    )

# Include routers
app.include_router(admissions.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
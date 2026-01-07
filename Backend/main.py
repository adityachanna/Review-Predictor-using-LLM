from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import router
from database import engine, Base
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Review Analysis API",
    description="API for submitting and analyzing customer reviews using AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include API router
app.include_router(router)

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Welcome to Review Analysis API",
        "docs": "/docs",
        "health": "OK"
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=4000, reload=True)

# Import load_dotenv to load environment variables
from dotenv import load_dotenv

# Load environment variables before app starts
load_dotenv()

# Import FastAPI
from fastapi import FastAPI

# Import CORS middleware
from fastapi.middleware.cors import CORSMiddleware

# Import chat router
from app.api.routes.chat_routes import router as chat_router

# Import review router
from app.api.routes.review_routes import router as review_router


# Create FastAPI app
app = FastAPI(
    title="OncoGuide Agentic AI API",
    version="0.2.0",
    description="FastAPI backend for OncoGuide cancer-related agentic AI system.",
)


# Add CORS settings for React frontend
app.add_middleware(
    CORSMiddleware,

    # Allow all frontend origins during local development
    allow_origins=["*"],

    # Do not use credentials when allowing all origins
    allow_credentials=False,

    # Allow all HTTP methods including OPTIONS and POST
    allow_methods=["*"],

    # Allow all headers used by fetch-event-source
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
def health_check():

    # Return backend health
    return {
        "status": "ok",
        "service": "OncoGuide API",
        "version": "0.2.0",
    }


# Include chat routes
app.include_router(chat_router)

# Include human review routes
app.include_router(review_router)
"""
Main entry point for the Personalized Networking Assistant FastAPI backend.

This module initializes the FastAPI application, configures middleware (CORS),
manages the database initialization lifecycle using context-based lifespans, 
and aggregates all service-specific API routing modules.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import engine, Base
from backend.routes import 
    generate, 
    factcheck, 
    history, 
    feedback
)

# Setup logging configuration
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("backend.app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    Initializes database tables and pre-warms ML models on start.
    """
    logger.info("Initializing application database tables...")
    try:
        # Create database tables if they do not exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
        
        # Check if the 'comment' column exists in 'history' table, if not, add it
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('history')]
        if 'comment' not in columns:
            logger.info("Altering history table to add comment column for backward compatibility...")
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE history ADD COLUMN comment VARCHAR"))
            logger.info("comment column added successfully.")
    except Exception as e:
        logger.error(f"Critical error initializing database tables: {e}")

    # Pre-warm ML models at startup so the first /generate request is not slow.
    # NOTE: Disabled on Render free tier (512 MB RAM) — loading DistilBERT + GPT-2
    # simultaneously at startup causes OOM before the server can accept requests.
    # The frontend uses a 180s timeout on /generate to handle lazy-load latency instead.
    # Uncomment below only if running on a machine with ≥2 GB available RAM.
    # logger.info("Pre-warming ML models (ThemeExtractor + ConversationGenerator)...")
    # try:
    #     from backend.routes.generate import theme_extractor, conversation_generator
    #     theme_extractor.initialize_model()
    #     conversation_generator.initialize_model()
    #     logger.info("ML models pre-warm complete.")
    # except Exception as e:
    #     logger.warning(f"ML model pre-warm failed (fallback templates will be used): {e}")
        
    yield
    
    logger.info("Application shutting down...")

# Instantiate FastAPI application with lifespan management and customized metadata
app = FastAPI(
    title="Personalized Networking Assistant API Service",
    description=(
        "A production-ready FastAPI service powering the Personalized Networking Assistant.\n\n"
        "### Key Capabilities:\n"
        "- **Conversation Starter Generation (GPT-2)**: Generates 3 contextual icebreaker questions.\n"
        "- **Theme Extraction (DistilBERT)**: Extracts dominant themes from event descriptions.\n"
        "- **Wikipedia Verification**: Validates professional and academic terms in real-time.\n"
        "- **Logs & Feedback**: Manages a historical SQLite log of inputs with user thumbs ratings and text comments."
    ),
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits requests from Streamlit's local ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes matching specs
app.include_router(generate.router, tags=["Conversation Starters"])
app.include_router(factcheck.router, tags=["Fact Checker"])
app.include_router(history.router, tags=["Conversation History"])
app.include_router(feedback.router, tags=["History Feedback"])

@app.get(
    "/", 
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Root health status endpoint"
)
async def health_check():
    """
    Verifies that the API service is active and responsive.
    """
    return {
        "status": "healthy",
        "app_name": "Personalized Networking Assistant Backend API",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "backend.app:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=True
    )

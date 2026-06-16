from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from yoink.api.routes import router

app = FastAPI(
    title="Yoink API",
    description="The Web backend for Yoink: Pack and sanitize codebases for LLMs.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Yoink API!",
        "docs": "/docs",
        "endpoints": {
            "/api/v1/sanitize": "POST - Sanitize a single file's content",
            "/api/v1/pack": "POST - Pack multiple files/contents",
            "/api/v1/pack-zip": "POST - Upload a ZIP codebase and pack it"
        }
    }

app.include_router(router)

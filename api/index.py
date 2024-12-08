import os
import sys
from pathlib import Path

# Add the root directory to Python path
root_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(root_dir)

from mangum import Mangum
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import traceback

try:
    from app.core.moderator import ContentModerator
except ImportError as e:
    print(f"Import Error: {str(e)}")
    print(f"Python Path: {sys.path}")
    print(f"Current Directory: {os.getcwd()}")
    raise

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class ModerateRequest(BaseModel):
    content: str

@app.get("/")
async def root():
    return {
        "message": "Modera API is running",
        "python_path": sys.path,
        "current_dir": os.getcwd(),
        "env_vars": {k: "set" if v else "not set" for k, v in os.environ.items() if "key" in k.lower()}
    }

@app.post("/api/moderate")
async def moderate_content(request: ModerateRequest):
    try:
        # Print debug information
        print("Received request with content length:", len(request.content))
        print("OpenAI API Key status:", "Set" if os.getenv("OPENAI_API_KEY") else "Not set")
        print("Current working directory:", os.getcwd())
        print("Python path:", sys.path)
        
        # Initialize moderator
        moderator = ContentModerator()
        
        # Process content
        result = moderator.moderate_content(request.content)
        
        # Ensure result is JSON serializable
        return JSONResponse(content=result)
    except Exception as e:
        error_detail = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "type": type(e).__name__,
            "debug_info": {
                "cwd": os.getcwd(),
                "python_path": sys.path,
                "env_vars": {k: "set" if v else "not set" for k, v in os.environ.items() if "key" in k.lower()}
            }
        }
        print("Error in moderation:", error_detail)
        return JSONResponse(
            status_code=500,
            content=error_detail
        )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_detail = {
        "error": str(exc),
        "traceback": traceback.format_exc(),
        "type": type(exc).__name__,
        "debug_info": {
            "cwd": os.getcwd(),
            "python_path": sys.path,
            "env_vars": {k: "set" if v else "not set" for k, v in os.environ.items() if "key" in k.lower()}
        }
    }
    print("Global exception:", error_detail)
    return JSONResponse(
        status_code=500,
        content=error_detail
    )

# Create handler for Vercel
handler = Mangum(app, lifespan="off")

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
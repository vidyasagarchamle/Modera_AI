import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.core.moderator import ContentModerator
import json
import traceback

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
    return {"message": "Modera API is running"}

@app.post("/api/moderate")
async def moderate_content(request: ModerateRequest):
    try:
        # Print debug information
        print("Received request with content length:", len(request.content))
        print("OpenAI API Key status:", "Set" if os.getenv("OPENAI_API_KEY") else "Not set")
        
        # Initialize moderator
        moderator = ContentModerator()
        
        # Process content
        result = moderator.moderate_content(request.content)
        
        # Ensure result is JSON serializable
        return JSONResponse(content=result)
    except Exception as e:
        error_detail = {
            "error": str(e),
            "traceback": traceback.format_exc()
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
        "traceback": traceback.format_exc()
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
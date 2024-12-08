import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.core.moderator import ContentModerator
import json

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
        # Initialize moderator
        moderator = ContentModerator()
        
        # Process content
        result = moderator.moderate_content(request.content)
        return result
    except Exception as e:
        print(f"Error in moderation: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)}
    )

# Create handler for Vercel
handler = Mangum(app, lifespan="off")

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
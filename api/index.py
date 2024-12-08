import os
from mangum import Mangum
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI
from bs4 import BeautifulSoup
import json
import traceback

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ModerateRequest(BaseModel):
    content: str

class ContentModerator:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        print(f"Initializing with API key: {self.api_key[:8]}...")
        self.client = OpenAI(api_key=self.api_key)

    def _extract_text_from_html(self, html_content: str) -> str:
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            print(f"Extracted text (first 100 chars): {text[:100]}...")
            return text
        except Exception as e:
            raise ValueError(f"Error parsing HTML content: {str(e)}")

    def _analyze_with_gpt4(self, text: str) -> dict:
        if not text.strip():
            return {
                "is_appropriate": True,
                "confidence_score": 1.0,
                "flagged_content": [],
                "moderation_summary": "Empty content provided."
            }

        try:
            print("Making API request to OpenAI...")
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """You are a content moderator. Analyze the following content and identify any inappropriate or concerning content. Focus on:
                    1. Hate speech or discriminatory language
                    2. Adult or explicit content
                    3. Violence or graphic content
                    4. Harassment or bullying
                    5. Spam or misleading information
                    
                    Provide a response in this exact JSON format:
                    {
                        "is_appropriate": true/false,
                        "confidence_score": 0.0-1.0,
                        "flagged_content": [
                            {
                                "type": "category of issue",
                                "severity": "low/medium/high",
                                "excerpt": "relevant text",
                                "explanation": "why this is an issue"
                            }
                        ],
                        "moderation_summary": "brief explanation of the decision"
                    }"""},
                    {"role": "user", "content": text}
                ],
                temperature=0.1
            )
            print("Received response from OpenAI")
            
            result = json.loads(response.choices[0].message.content)
            required_fields = ["is_appropriate", "confidence_score", "flagged_content", "moderation_summary"]
            if not all(field in result for field in required_fields):
                raise ValueError("Invalid response format from GPT-4")
                
            return result
        except Exception as e:
            print(f"OpenAI API Error Details: {str(e)}")
            raise Exception(f"Error analyzing content with GPT-4: {str(e)}")

    def moderate_content(self, html_content: str) -> dict:
        if not html_content:
            raise ValueError("HTML content cannot be empty")
            
        # Extract text from HTML
        text_content = self._extract_text_from_html(html_content)
        
        # Analyze content using GPT-4
        moderation_result = self._analyze_with_gpt4(text_content)
        
        return moderation_result

@app.get("/")
async def root():
    return {
        "message": "Modera API is running",
        "openai_key_status": "Set" if os.getenv("OPENAI_API_KEY") else "Not set",
        "env_vars": {k: "set" if v else "not set" for k, v in os.environ.items() if "key" in k.lower()}
    }

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
            "traceback": traceback.format_exc(),
            "type": type(e).__name__
        }
        print("Error in moderation:", error_detail)
        return JSONResponse(
            status_code=500,
            content=error_detail
        )

# Create handler for Vercel
handler = Mangum(app, lifespan="off")
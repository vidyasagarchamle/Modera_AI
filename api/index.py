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
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        try:
            self.api_key = os.getenv("OPENAI_API_KEY")
            logger.info(f"API Key present: {bool(self.api_key)}")
            if not self.api_key:
                raise ValueError("OpenAI API key not found in environment variables")
            if not self.api_key.startswith('sk-'):
                raise ValueError("Invalid OpenAI API key format. Key should start with 'sk-'")
            logger.info(f"Initializing with API key starting with: {self.api_key[:5]}...")
            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Error in ContentModerator initialization: {str(e)}")
            raise

    def _extract_text_from_html(self, html_content: str) -> str:
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            logger.info(f"Extracted text length: {len(text)}")
            return text
        except Exception as e:
            logger.error(f"Error in HTML parsing: {str(e)}")
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
            logger.info("Making API request to OpenAI...")
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
            logger.info("Received response from OpenAI")
            
            result = json.loads(response.choices[0].message.content)
            required_fields = ["is_appropriate", "confidence_score", "flagged_content", "moderation_summary"]
            if not all(field in result for field in required_fields):
                raise ValueError("Invalid response format from GPT-4")
            
            logger.info("Successfully parsed GPT-4 response")
            return result
        except Exception as e:
            logger.error(f"Error in GPT-4 analysis: {str(e)}")
            raise Exception(f"Error analyzing content with GPT-4: {str(e)}")

    def moderate_content(self, html_content: str) -> dict:
        if not html_content:
            raise ValueError("HTML content cannot be empty")
        
        try:
            # Extract text from HTML
            text_content = self._extract_text_from_html(html_content)
            
            # Analyze content using GPT-4
            moderation_result = self._analyze_with_gpt4(text_content)
            
            return moderation_result
        except Exception as e:
            logger.error(f"Error in content moderation: {str(e)}")
            raise

@app.get("/")
async def root():
    try:
        api_key = os.getenv("OPENAI_API_KEY", "")
        key_status = "Invalid" if not api_key.startswith("sk-") else "Valid"
        return {
            "message": "Modera API is running",
            "openai_key_status": key_status,
            "key_prefix": api_key[:4] if api_key else "None",
            "env_vars": {k: "set" if v else "not set" for k, v in os.environ.items() if "key" in k.lower()}
        }
    except Exception as e:
        logger.error(f"Error in root endpoint: {str(e)}")
        return {"error": str(e)}

@app.post("/api/moderate")
async def moderate_content(request: ModerateRequest):
    try:
        # Log request information
        logger.info(f"Received request with content length: {len(request.content)}")
        logger.info(f"OpenAI API Key status: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not set'}")
        
        # Initialize moderator
        moderator = ContentModerator()
        
        # Process content
        result = moderator.moderate_content(request.content)
        
        # Log success
        logger.info("Successfully processed moderation request")
        
        # Return result
        return JSONResponse(content=result)
    except Exception as e:
        # Log the full error
        logger.error(f"Error in moderation endpoint: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return error response
        error_detail = {
            "error": str(e),
            "type": type(e).__name__,
            "details": traceback.format_exc()
        }
        return JSONResponse(
            status_code=500,
            content=error_detail
        )

# Create handler for Vercel
handler = Mangum(app, lifespan="off")
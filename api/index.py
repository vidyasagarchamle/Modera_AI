from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from openai import OpenAI
from bs4 import BeautifulSoup
from mangum import Mangum
import os
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

# HTML content for the test interface
TEST_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Content Moderation Test</title>
    <script>
        async function testModeration() {
            const content = document.getElementById('content').value;
            const result = document.getElementById('result');
            const debugInfo = document.getElementById('debug');
            
            try {
                debugInfo.innerHTML = 'Sending request...\\n';
                const response = await fetch('/api/moderate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ content: content })
                });
                
                debugInfo.innerHTML += `Response status: ${response.status}\\n`;
                const responseData = await response.json();
                debugInfo.innerHTML += `Raw response: ${JSON.stringify(responseData, null, 2)}\\n\\n`;
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}, details: ${JSON.stringify(responseData)}`);
                }
                
                result.innerHTML = `
                    <h3>Moderation Result:</h3>
                    <p>Is Appropriate: ${responseData.is_appropriate}</p>
                    <p>Confidence Score: ${responseData.confidence_score}</p>
                    <h4>Flagged Content:</h4>
                    ${responseData.flagged_content.length ? 
                        responseData.flagged_content.map(flag => `
                            <div class="flag">
                                <p>Type: ${flag.type}</p>
                                <p>Severity: ${flag.severity}</p>
                                <p>Excerpt: ${flag.excerpt}</p>
                                <p>Explanation: ${flag.explanation}</p>
                            </div>
                        `).join('') : 
                        '<p>No content flagged</p>'
                    }
                    <h4>Summary:</h4>
                    <p>${responseData.moderation_summary}</p>
                `;
            } catch (error) {
                result.innerHTML = `<p style="color: red">Error: ${error.message}</p>`;
                debugInfo.innerHTML += `Error caught: ${error.message}\\n`;
                if (error.stack) {
                    debugInfo.innerHTML += `Error stack: ${error.stack}\\n`;
                }
            }
        }

        window.onload = function() {
            const exampleContent = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Inappropriate Content</title>
</head>
<body>
    <h1>Welcome to Our Fake Website</h1>
    <p>This website is designed to demonstrate inappropriate content detection.</p>
    
    <!-- Offensive Language -->
    <p>Example of offensive language: "You're so stupid and useless."</p>
    
    <!-- Explicit Material -->
    <p>Explicit description: "This image gallery contains adult-only content."</p>
    
    <!-- Phishing Link -->
    <a href="http://fakebank-login.com">Login to your bank account</a>
    
    <!-- Spam Content -->
    <div>
        <p>Buy now! Limited offer!</p>
        <p>Buy now! Limited offer!</p>
        <p>Buy now! Limited offer!</p>
    </div>
</body>
</html>`;
            document.getElementById('content').value = exampleContent;
        }
    </script>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        textarea {
            width: 100%;
            height: 300px;
            margin: 10px 0;
            font-family: monospace;
            padding: 10px;
        }
        button {
            padding: 10px 20px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #0056b3;
        }
        .flag {
            border: 1px solid #ddd;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            background-color: #fff8f8;
        }
        #debug {
            margin-top: 20px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 5px;
            font-family: monospace;
            font-size: 14px;
            white-space: pre-wrap;
            overflow-wrap: break-word;
        }
        #result {
            margin-top: 20px;
        }
        h1 {
            color: #333;
        }
        .instructions {
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <h1>Content Moderation Test Interface</h1>
    <div class="instructions">
        <p>This interface allows you to test the content moderation API. Enter your HTML content in the textarea below and click "Test Moderation" to see the results.</p>
        <p>The example content demonstrates various types of potentially inappropriate content for testing.</p>
    </div>
    <textarea id="content" placeholder="Enter HTML content to moderate..."></textarea>
    <br>
    <button onclick="testModeration()">Test Moderation</button>
    <div id="debug"></div>
    <div id="result"></div>
</body>
</html>
"""

@app.get("/")
async def serve_test_interface():
    """Serve the test interface"""
    return HTMLResponse(content=TEST_HTML, status_code=200)

@app.post("/api/moderate")
async def moderate_content(request: ModerateRequest):
    """Content moderation endpoint"""
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
handler = Mangum(app)
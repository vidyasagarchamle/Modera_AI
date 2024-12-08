from http.server import BaseHTTPRequestHandler
from openai import OpenAI
from bs4 import BeautifulSoup
import os
import json

def moderate_content(html_content):
    try:
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"error": "OpenAI API key not found"}
        client = OpenAI(api_key=api_key)
        
        # Extract text from HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        
        # Analyze with GPT-4
        response = client.chat.completions.create(
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
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

def handler(request):
    if request.method == "OPTIONS":
        # Handle CORS preflight request
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
        return {"statusCode": 204, "headers": headers}

    if request.method == "POST":
        try:
            # Parse request body
            body = json.loads(request.body)
            
            if not body.get("content"):
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "No content provided"})
                }
            
            # Process content
            result = moderate_content(body["content"])
            
            # Return response
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps(result)
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": str(e)})
            }
    
    # Handle unsupported methods
    return {
        "statusCode": 405,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": "Method not allowed"})
    }
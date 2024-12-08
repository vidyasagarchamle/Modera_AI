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
                    "status": "flagged" or "good_to_go",
                    "issues": [
                        {
                            "type": "hate_speech/adult_content/violence/harassment/spam",
                            "severity": "low/medium/high",
                            "description": "brief description of why this content is problematic"
                        }
                    ]
                }
                
                Notes:
                - If content is appropriate, return status as "good_to_go" and empty issues array
                - If content is inappropriate, return status as "flagged" and include all detected issues
                - Be specific in descriptions but avoid repeating the problematic content
                """},
                {"role": "user", "content": text}
            ],
            temperature=0.1
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
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
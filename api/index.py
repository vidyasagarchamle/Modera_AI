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

class handler(BaseHTTPRequestHandler):
    def _send_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            # Serve the HTML interface
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('test.html', 'r') as f:
                self.wfile.write(f.read().encode())
        else:
            self._send_response(404, {"error": "Not found"})

    def do_POST(self):
        if self.path == "/api/moderate":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode())
                
                if not request_data.get("content"):
                    self._send_response(400, {"error": "No content provided"})
                    return
                
                result = moderate_content(request_data["content"])
                self._send_response(200, result)
            except Exception as e:
                self._send_response(500, {"error": str(e)})
        else:
            self._send_response(404, {"error": "Not found"})
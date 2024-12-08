from openai import OpenAI
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import os
import json
from dotenv import load_dotenv

load_dotenv()

class ContentModerator:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        self.client = OpenAI(api_key=api_key)

    def _extract_text_from_html(self, html_content: str) -> str:
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text(separator=' ', strip=True)
        except Exception as e:
            raise ValueError(f"Error parsing HTML content: {str(e)}")

    def _analyze_with_gpt4(self, text: str) -> Dict[str, Any]:
        if not text.strip():
            return {
                "status": "good_to_go",
                "issues": []
            }

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """You are a content moderator. Analyze the following content and identify any issues related to:
                    1. Hate speech or offensive language
                    2. Explicit material (nudity, explicit language)
                    3. Phishing links or deceptive content
                    4. Repetitive spam or irrelevant content
                    
                    Return a JSON response with:
                    {
                        "status": "flagged" or "good_to_go",
                        "issues": [
                            {
                                "type": "issue type",
                                "severity": "low/medium/high",
                                "description": "brief description"
                            }
                        ]
                    }
                    
                    If no issues are found, return status as "good_to_go" with an empty issues list."""},
                    {"role": "user", "content": text}
                ],
                temperature=0.1,
                response_format={ "type": "json_object" }
            )
            
            result = json.loads(response.choices[0].message.content)
            # Validate the response format
            if "status" not in result or "issues" not in result:
                raise ValueError("Invalid response format from GPT-4")
                
            return result
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON response from GPT-4")
        except Exception as e:
            raise Exception(f"Error analyzing content with GPT-4: {str(e)}")

    def moderate_content(self, html_content: str) -> Dict[str, Any]:
        if not html_content:
            raise ValueError("HTML content cannot be empty")
            
        # Extract text from HTML
        text_content = self._extract_text_from_html(html_content)
        
        # Analyze content using GPT-4
        moderation_result = self._analyze_with_gpt4(text_content)
        
        return moderation_result 
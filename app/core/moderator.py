from openai import OpenAI
from bs4 import BeautifulSoup
from typing import Dict, Any
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
                "is_appropriate": True,
                "confidence_score": 1.0,
                "flagged_content": [],
                "moderation_summary": "Empty content provided."
            }

        try:
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
            
            result = json.loads(response.choices[0].message.content)
            required_fields = ["is_appropriate", "confidence_score", "flagged_content", "moderation_summary"]
            if not all(field in result for field in required_fields):
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
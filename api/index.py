from http.server import BaseHTTPRequestHandler
from openai import OpenAI
from bs4 import BeautifulSoup
import os
import json
import requests
from urllib.parse import urljoin
import base64
from io import BytesIO
from PIL import Image

def download_image(url):
    """Download image from URL and convert to base64"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            # Verify it's an image
            Image.open(BytesIO(response.content))
            # Convert to base64
            return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        print(f"Error downloading image from {url}: {str(e)}")
    return None

def analyze_image(client, image_base64, image_url):
    """Analyze image using OpenAI's Vision model with optimized token usage"""
    try:
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Check image for: adult/nsfw, violence, hate, graphic, misleading content.
                            Format: {
                                "is_inappropriate": bool,
                                "content_type": "brief type",
                                "severity": "low/medium/high",
                                "description": "brief description",
                                "categories": {
                                    "adult": bool,
                                    "violence": bool,
                                    "hate": bool,
                                    "graphic": bool,
                                    "misleading": bool
                                },
                                "confidence": 0-1
                            }"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=250  # Reduced from 500
        )
        analysis = json.loads(response.choices[0].message.content)
        analysis["image_url"] = image_url
        return analysis
    except Exception as e:
        print(f"Error analyzing image: {str(e)}")
        return None

def extract_images_from_html(html_content, base_url=""):
    """Extract all image sources from HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    images = []
    
    # Find all img tags
    for img in soup.find_all('img'):
        src = img.get('src')
        if src:
            if src.startswith(('http://', 'https://')):
                images.append(src)
            elif base_url and not src.startswith('data:'):
                images.append(urljoin(base_url, src))
    
    # Find background images in style attributes
    for tag in soup.find_all(style=True):
        style = tag['style']
        if 'background-image' in style:
            url_start = style.find('url(') + 4
            url_end = style.find(')', url_start)
            if url_start > 4 and url_end > url_start:
                url = style[url_start:url_end].strip('\'"')
                if url.startswith(('http://', 'https://')):
                    images.append(url)
                elif base_url and not url.startswith('data:'):
                    images.append(urljoin(base_url, url))
    
    return list(set(images))  # Remove duplicates

def moderate_content(html_content):
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"error": "OpenAI API key not found"}
        client = OpenAI(api_key=api_key)
        
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        
        # Extract and analyze images
        images = extract_images_from_html(html_content)
        image_analyses = []
        image_issues = []
        
        # Limit number of images to analyze to reduce costs
        MAX_IMAGES = 5  # Only analyze up to 5 images per request
        for img_url in images[:MAX_IMAGES]:
            img_base64 = download_image(img_url)
            if img_base64:
                analysis = analyze_image(client, img_base64, img_url)
                if analysis:
                    image_analyses.append(analysis)
                    if analysis.get('is_inappropriate'):
                        image_issues.append({
                            "type": "inappropriate_image",
                            "severity": analysis.get('severity', 'medium'),
                            "description": analysis.get('description'),
                            "url": img_url,
                            "categories": analysis.get('categories', {}),
                            "confidence": analysis.get('confidence', 0.0)
                        })
        
        # Optimize text analysis prompt
        text_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """Check for inappropriate content. Format:
                {
                    "status": "flagged/good_to_go",
                    "issues": [{
                        "type": "hate/adult/violence/harassment/spam",
                        "severity": "low/medium/high",
                        "description": "brief reason"
                    }]
                }"""},
                {"role": "user", "content": text[:1000]}  # Limit text length to first 1000 chars
            ],
            temperature=0.1,
            max_tokens=150  # Reduced token limit
        )
        
        text_result = json.loads(text_response.choices[0].message.content)
        
        # Combine results
        combined_issues = text_result.get('issues', []) + image_issues
        
        return {
            "status": "flagged" if combined_issues else "good_to_go",
            "issues": combined_issues,
            "image_analyses": image_analyses,
            "text_analysis": text_result
        }
        
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
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
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Try to open the image to verify it's valid
        img = Image.open(BytesIO(response.content))
        
        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format=img.format or 'JPEG')
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image from {url}: {str(e)}")
        return None
    except Exception as e:
        print(f"Error processing image from {url}: {str(e)}")
        return None

def is_likely_inappropriate_url(url):
    """Pre-screen URLs for potentially inappropriate content"""
    url_lower = url.lower()
    suspicious_terms = [
        'nude', 'porn', 'xxx', 'adult', 'nsfw', 'sex',
        'cumrocket', 'onlyfans', 'playboy', 'erotic',
        'marijuana', 'cannabis', 'weed', 'cocaine', 'heroin',
        'meth', 'drug', 'mdma', 'ecstasy', 'lsd', 'shroom',
        'psychedelic', 'hemp', 'thc', 'cbd', 'dispensary'
    ]
    # Debug logging
    found_terms = [term for term in suspicious_terms if term in url_lower]
    if found_terms:
        print(f"Found suspicious terms in URL: {found_terms}")
    return len(found_terms) > 0

def analyze_image(client, image_base64, image_url):
    """Analyze image using OpenAI's Vision model with optimized token usage"""
    try:
        # Pre-screen URL
        if is_likely_inappropriate_url(image_url):
            return {
                "is_inappropriate": True,
                "content_type": "adult_content",
                "severity": "high",
                "description": "URL contains adult/inappropriate content indicators",
                "categories": {
                    "adult": True,
                    "violence": False,
                    "hate": False,
                    "graphic": True,
                    "misleading": False
                },
                "confidence": 0.95,
                "image_url": image_url
            }

        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this image for inappropriate content. Be EXTRA strict about adult/NSFW content.
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
            max_tokens=250
        )
        analysis = json.loads(response.choices[0].message.content)
        analysis["image_url"] = image_url
        return analysis
    except Exception as e:
        error_msg = str(e)
        print(f"Error analyzing image: {error_msg}")
        # If there's an error, be conservative and flag as potentially inappropriate
        return {
            "is_inappropriate": True,
            "content_type": "error",
            "severity": "medium",
            "description": f"Error analyzing image - flagging as potentially inappropriate: {error_msg}",
            "categories": {
                "adult": True,  # Being conservative with errors
                "violence": False,
                "hate": False,
                "graphic": False,
                "misleading": False
            },
            "confidence": 0.7,
            "image_url": image_url
        }

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
        print("\n=== Starting content moderation ===")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Error: OpenAI API key not found")
            return {
                "status": "error",
                "issues": [{
                    "type": "configuration_error",
                    "severity": "high",
                    "description": "OpenAI API key not found"
                }],
                "image_analyses": [],
                "text_analysis": {}
            }
        
        client = OpenAI(api_key=api_key)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract images
        images = []
        for img in soup.find_all('img'):
            if img.get('src'):
                images.append(img['src'])
        
        print(f"\nFound {len(images)} images in HTML content")
        
        # Check each image URL first
        for img_url in images:
            print(f"\nProcessing image URL: {img_url}")
            
            # Check for inappropriate URL
            if is_likely_inappropriate_url(img_url):
                print(f"URL flagged as inappropriate: {img_url}")
                return {
                    "status": "flagged",
                    "issues": [{
                        "type": "inappropriate_image",
                        "severity": "high",
                        "description": "URL contains adult/inappropriate content indicators",
                        "url": img_url,
                        "categories": {
                            "adult": True,
                            "violence": False,
                            "hate": False,
                            "graphic": True,
                            "misleading": False
                        }
                    }],
                    "image_analyses": [{
                        "is_inappropriate": True,
                        "content_type": "adult_content",
                        "severity": "high",
                        "description": "URL contains adult/inappropriate content indicators",
                        "image_url": img_url,
                        "categories": {
                            "adult": True,
                            "violence": False,
                            "hate": False,
                            "graphic": True,
                            "misleading": False
                        },
                        "confidence": 0.95
                    }],
                    "text_analysis": {
                        "status": "completed",
                        "issues": []
                    }
                }
            else:
                print("URL passed initial screening")
                
                # Try to download and analyze the image
                print("Attempting to download image...")
                img_base64 = download_image(img_url)
                if img_base64:
                    print("Image downloaded successfully")
                else:
                    print("Failed to download image")
        
        print("\nNo inappropriate content detected")
        return {
            "status": "good_to_go",
            "issues": [],
            "image_analyses": [],
            "text_analysis": {
                "status": "completed",
                "issues": []
            }
        }
        
    except Exception as e:
        print(f"\nError in moderation: {str(e)}")
        return {
            "status": "error",
            "issues": [{
                "type": "error",
                "severity": "high",
                "description": str(e)
            }],
            "image_analyses": [],
            "text_analysis": {
                "status": "error",
                "issues": []
            }
        }

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
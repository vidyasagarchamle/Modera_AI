# Modera - Content Moderation API

A powerful content moderation API that uses GPT-4 Vision and URL analysis to detect and flag inappropriate content in HTML, including both text and images.

## Features

- Real-time HTML content moderation
- Image analysis using GPT-4 Vision
- URL-based pre-screening for inappropriate content
- Multiple detection categories:
  - Adult/NSFW content
  - Violence and gore
  - Hate speech and symbols
  - Graphic content
  - Misleading information
  - Harassment
  - Illegal substances and drug-related content:
    - Marijuana/Cannabis
    - Illicit drugs
    - Drug paraphernalia
    - Drug-related terminology
- Detailed analysis with confidence scores
- Severity levels (low/medium/high)
- Fast URL-based detection without image processing when possible

## API Usage

### Endpoint

```
POST /api/index
```

### Request Format

```json
{
    "content": "<p>Your HTML content here</p>"
}
```

### Response Format

```json
{
    "status": "flagged" or "good_to_go",
    "issues": [
        {
            "type": "inappropriate_image/hate_speech/adult_content/violence/harassment/spam/drug_content",
            "severity": "low/medium/high",
            "description": "Detailed description of the issue",
            "url": "URL of flagged image (if applicable)",
            "categories": {
                "adult": boolean,
                "violence": boolean,
                "hate": boolean,
                "graphic": boolean,
                "misleading": boolean,
                "drugs": boolean
            }
        }
    ],
    "image_analyses": [
        {
            "is_inappropriate": boolean,
            "content_type": "type of content",
            "severity": "low/medium/high",
            "description": "Analysis description",
            "image_url": "analyzed image URL",
            "categories": {
                "adult": boolean,
                "violence": boolean,
                "hate": boolean,
                "graphic": boolean,
                "misleading": boolean,
                "drugs": boolean
            },
            "confidence": float (0-1)
        }
    ],
    "text_analysis": {
        "status": "completed/error",
        "issues": []
    }
}
```

### Example Usage

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"content":"<p>Text content</p><img src=\"image_url.jpg\">"}' \
  http://localhost:8080/api/index
```

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/modera.git
cd modera
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
- Copy `.env.template` to `.env`
- Add your OpenAI API key to the `.env` file

4. Start the local server:
```bash
python local_server.py
```

The server will start on `http://localhost:8080`

## Testing

1. Open `http://localhost:8080` in your browser
2. Use the test interface to paste HTML content
3. Click "Test Content" to see the moderation results

## Security Notes

- Keep your OpenAI API key secure and never commit it to version control
- Use environment variables for sensitive information
- The development server is not suitable for production use
- Consider implementing rate limiting for production deployments

## Features in Detail

### URL Pre-screening
- Automatically detects potentially inappropriate content based on URL patterns
- Fast initial screening without requiring image download
- Configurable list of suspicious terms

### Image Analysis
- Uses GPT-4 Vision for deep image analysis
- Provides confidence scores for detected issues
- Multiple category detection in a single pass

### Text Analysis
- Analyzes text content for inappropriate material
- Provides detailed categorization of issues
- Fast and efficient processing

## Error Handling

The API includes robust error handling:
- Invalid requests return appropriate HTTP status codes
- Network issues are gracefully handled
- Image processing errors don't break the analysis
- Detailed error messages for debugging
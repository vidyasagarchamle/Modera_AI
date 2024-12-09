# Modera - Content Moderation API

A FastAPI-based content moderation API that uses GPT-4 to analyze and moderate HTML content.

## Features

- Real-time HTML content moderation using GPT-4
- Analysis of multiple content categories:
  - Hate speech
  - Adult content
  - Violence
  - Harassment
  - Spam/misleading information
- Severity levels (low/medium/high) for each issue
- Detailed descriptions of identified issues

## API Usage

### Endpoint

```
POST /api/moderate
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
            "type": "hate_speech/adult_content/violence/harassment/spam",
            "severity": "low/medium/high",
            "description": "brief description of why this content is problematic"
        }
    ]
}
```

Note: If no issues are found, the `issues` array will be empty and `status` will be "good_to_go".

### Example Usage

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"content":"<p>Your content to moderate</p>"}' \
  https://your-api-endpoint/api/moderate
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

## Security Notes

- Keep your OpenAI API key secure and never commit it to version control
- Use environment variables for sensitive information
- The development server is not suitable for production use
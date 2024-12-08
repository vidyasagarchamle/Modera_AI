# Modera - Content Moderation API

A FastAPI-based content moderation API that uses GPT-4 to analyze and moderate HTML content.

## Setup

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

3. Create a `.env` file:
- Copy `.env.template` to `.env`
- Add your OpenAI API key to the `.env` file

## Running the API

### Local Development Server
```bash
python local_server.py
```
This will start a Flask development server at `http://127.0.0.1:8000` with a test interface.

### Production Server
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://127.0.0.1:8000`

## API Endpoints

### POST /api/moderate

Moderates HTML content and returns a moderation result.

**Request Body:**
```json
{
    "content": "<p>Your HTML content here</p>"
}
```

**Response Format:**
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

## Testing

1. Using the Web Interface:
- Start the local server: `python local_server.py`
- Open `http://127.0.0.1:8000` in your browser
- Use the provided test interface to input HTML content
- View color-coded results with detailed issue descriptions

2. Using Python Test Script:
```bash
python test_api.py
```

3. Using cURL:
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"content":"<p>Test content</p>"}' \
  http://127.0.0.1:8000/api/index
```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)

## Deployment

The API is configured for deployment on Vercel. The `vercel.json` file contains the necessary configuration.

## Features

- Real-time HTML content moderation using GPT-4
- Analysis of multiple content categories:
  - Hate speech
  - Adult content
  - Violence
  - Harassment
  - Spam/misleading information
- Severity levels (low/medium/high) for each issue
- User-friendly web interface for testing
- Color-coded results for better visualization
- Detailed descriptions of identified issues

## Security Notes

- Keep your OpenAI API key secure and never commit it to version control
- Use environment variables for sensitive information
- The development server is not suitable for production use
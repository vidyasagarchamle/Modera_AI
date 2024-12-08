# Modera API

A content moderation API that analyzes HTML content using GPT-4 to check against predefined content moderation guidelines.

## Features

- HTML content analysis
- Content moderation using GPT-4
- Detects hate speech, explicit content, phishing, and spam
- Severity-based issue categorization
- RESTful API interface

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the root directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Running the API

Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /api/v1/moderate

Analyzes HTML content for moderation issues.

**Request Body:**
```json
{
    "content": "<html>Your HTML content here</html>"
}
```

**Response:**
```json
{
    "status": "flagged",
    "issues": [
        {
            "type": "hate_speech",
            "severity": "high",
            "description": "Contains offensive language"
        }
    ]
}
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc` 
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

1. Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

2. The API will be available at `http://localhost:8000`

## API Endpoints

### POST /api/moderate

Moderates HTML content and returns a moderation result.

**Request Body:**
```json
{
    "content": "<p>Your HTML content here</p>"
}
```

**Response:**
```json
{
    "is_appropriate": true,
    "confidence_score": 0.95,
    "flagged_content": [
        {
            "type": "category of issue",
            "severity": "low/medium/high",
            "excerpt": "relevant text",
            "explanation": "why this is an issue"
        }
    ],
    "moderation_summary": "Brief explanation of the decision"
}
```

## Testing

1. Using Python:
```bash
python local_test.py
```

2. Using the HTML interface:
- Open `test.html` in your browser
- Enter HTML content in the textarea
- Click "Test Moderation" to see results

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)

## Deployment

The API is configured for deployment on Vercel. The `vercel.json` file contains the necessary configuration.

## Notes

- The API uses GPT-4 for content moderation
- Make sure to keep your OpenAI API key secure and never commit it to version control
- The API analyzes HTML content for:
  - Hate speech
  - Adult content
  - Violence
  - Harassment
  - Spam/misleading information
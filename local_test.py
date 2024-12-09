import os
from dotenv import load_dotenv
from app.core.moderator import ContentModerator

def test_moderation():
    # Load environment variables and print debug info
    load_dotenv()
    print("All environment variables:")
    for key, value in os.environ.items():
        if "KEY" in key:  # Only print variables containing "KEY" for security
            print(f"{key}: {value[:10]}...")
    
    # Create an instance of the moderator
    try:
        moderator = ContentModerator()
    except Exception as e:
        print(f"Error creating moderator: {str(e)}")
        return
    
    # Test cases
    test_cases = [
        {
            "name": "Simple Test",
            "content": "<p>This is a simple test content.</p>"
        },
        {
            "name": "Complex Test",
            "content": """
                <article>
                    <h1>Test Article</h1>
                    <p>This is a more complex test with multiple paragraphs.</p>
                    <p>It includes various HTML elements and formatting.</p>
                </article>
            """
        }
    ]
    
    # Run tests
    for test in test_cases:
        print(f"\nTesting: {test['name']}")
        print("-" * 50)
        try:
            result = moderator.moderate_content(test['content'])
            print("Result:")
            print(f"Is Appropriate: {result['is_appropriate']}")
            print(f"Confidence Score: {result['confidence_score']}")
            print("\nFlagged Content:")
            if result['flagged_content']:
                for flag in result['flagged_content']:
                    print(f"- Type: {flag['type']}")
                    print(f"  Severity: {flag['severity']}")
                    print(f"  Excerpt: {flag['excerpt']}")
                    print(f"  Explanation: {flag['explanation']}\n")
            else:
                print("No content flagged")
            print(f"\nSummary: {result['moderation_summary']}")
        except Exception as e:
            print(f"Error: {str(e)}")
        print("-" * 50)

if __name__ == "__main__":
    test_moderation() 
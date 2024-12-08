import requests
import json

# Updated Vercel deployment URL
API_URL = "https://modera-git-main-vidyasagarchamles-projects.vercel.app/moderate"

def test_direct_html():
    """Test with direct HTML content"""
    html_content = """
    <div class="article">
        <h1>Sample Article</h1>
        <p>This is a test article with some content that needs moderation.</p>
        <p>It may contain inappropriate content like violence or adult themes.</p>
    </div>
    """
    
    payload = {"content": html_content}
    try:
        response = requests.post(API_URL, json=payload)
        print("\nDirect HTML Test Results:")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error testing direct HTML: {str(e)}")
        print(f"Response status code: {response.status_code}")
        print(f"Response text: {response.text}")

def test_from_file(file_path):
    """Test with HTML content from a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
            
        payload = {"content": html_content}
        response = requests.post(API_URL, json=payload)
        print(f"\nFile Test Results for {file_path}:")
        print(json.dumps(response.json(), indent=2))
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
    except Exception as e:
        print(f"Error: {str(e)}")
        if 'response' in locals():
            print(f"Response status code: {response.status_code}")
            print(f"Response text: {response.text}")

if __name__ == "__main__":
    # Test with direct HTML
    test_direct_html()
    
    # Test with the sample HTML file
    test_from_file("test.html")
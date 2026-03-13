import os
import google.generativeai as genai

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # Try getting from the .env if it's not exported
    from dotenv import load_dotenv
    load_dotenv(os.path.join("e:\\Internship\\Agent-8", ".env"))
    api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

try:
    # Attempt 1: Using GenerativeModel (Gemini style)
    model = genai.GenerativeModel('imagen-3.0-generate-001')
    print("Testing generate_content with imagen-3.0-generate-001...")
    result = model.generate_content("A simple blue square")
    print("Success with GenerativeModel!")
except Exception as e:
    print(f"Failed with GenerativeModel: {e}")

try:
    print("\nTesting generate_image API...")
    result = genai.generate_image(prompt="A simple red square")
    print("Success with generate_image!")
except Exception as e:
    print(f"Failed with generate_image: {e}")

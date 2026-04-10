import sys
import os
import google.generativeai as genai

def main():
    if len(sys.argv) < 3:
        print("Missing arguments")
        sys.exit(1)
        
    prompt = sys.argv[1]
    output_filepath = sys.argv[2]
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Missing GEMINI_API_KEY")
        sys.exit(1)
        
    genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel('gemini-3.1-flash-image-preview')
        result = model.generate_content(
            prompt,
            generation_config={"response_modalities": ["IMAGE"]}
        )
        
        img_part = result.parts[0]
        if hasattr(img_part, 'inline_data') and img_part.inline_data:
            with open(output_filepath, 'wb') as f:
                f.write(img_part.inline_data.data)
            print("SUCCESS")
        else:
            print("No inline_data found.")
            sys.exit(2)
    except Exception as e:
        print(str(e))
        sys.exit(3)

if __name__ == "__main__":
    main()

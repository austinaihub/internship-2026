from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState
import os

class PublisherAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    def publish_post(self, state: AgentState):
        """
        Formats and publishes the final post.
        """
        print("--- PUBLISHER: Finalizing and Publishing ---")
        
        post_text = state.get("post_text")
        image_path = state.get("image_path")
        
        if not post_text or not image_path:
            return {"status": "error", "feedback": "Missing text or image for publication."}

        # 1. Format the post (ensure character limits, hashtags)
        formatter_prompt = ChatPromptTemplate.from_template(
            """
            You are a Social Media Manager.
            Format the following post for X (Twitter) and Instagram.
            
            STRUCTURE:
            1. Start with the header: **X (Twitter):**
            2. Provide the X version (max 280 characters).
            3. Then the header: **Instagram:**
            4. Provide the Instagram version.
            
            Add 2-3 relevant hashtags to each.
            
            Original Text:
            {text}
            
            Return the final formatted text with these exact headers.
            """
        )
        
        chain = formatter_prompt | self.llm
        final_text = chain.invoke({"text": post_text}).content
        print(f"Final Text to Publish:\n{final_text}")
        print(f"Image to Publish: {image_path}")

        # 2. Publish (Simulated for now)
        # We simulate the publication by creating a beautiful HTML preview
        
        # Simple Markdown-ish to HTML conversion for the preview
        formatted_html_text = final_text.replace("**X (Twitter):**", "<h3 style='color: #1DA1F2; border-bottom: 2px solid #1DA1F2; padding-bottom: 5px;'>X (Twitter)</h3>")
        formatted_html_text = formatted_html_text.replace("**Instagram:**", "<h3 style='color: #E1306C; border-bottom: 2px solid #E1306C; padding-bottom: 5px; margin-top: 20px;'>Instagram</h3>")
        formatted_html_text = formatted_html_text.replace("\n", "<br>")

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #f0f2f5; margin: 0; }}
                .container {{ display: flex; flex-direction: column; gap: 20px; align-items: center; padding: 40px; }}
                .post-card {{ background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); max-width: 500px; padding: 25px; transition: transform 0.2s; }}
                .post-card:hover {{ transform: translateY(-5px); }}
                .post-header {{ font-weight: bold; margin-bottom: 15px; display: flex; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                .avatar {{ width: 45px; height: 45px; background: linear-gradient(45deg, #1DA1F2, #E1306C); border-radius: 50%; margin-right: 12px; }}
                .post-text {{ font-size: 15px; line-height: 1.6; color: #333; }}
                .post-image {{ width: 100%; border-radius: 8px; margin-top: 20px; border: 1px solid #eee; }}
                .post-footer {{ color: #888; font-size: 12px; margin-top: 15px; display: flex; justify-content: space-between; }}
                h3 {{ margin: 10px 0; font-size: 18px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="post-card">
                    <div class="post-header">
                        <div class="avatar"></div>
                        <div>
                            <div style="font-size: 16px;">Awareness Agent System</div>
                            <div style="font-weight: normal; color: #777; font-size: 13px;">@humanitarian_bot</div>
                        </div>
                    </div>
                    <div class="post-text">{formatted_html_text}</div>
                    <img src="{os.path.abspath(image_path)}" class="post-image" alt="Generated Content">
                    <div class="post-footer">
                        <span>Just now · Global Outreach</span>
                        <span>🚀 Published</span>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"post_preview_{timestamp}.html"
        output_dir = os.getenv("OUTPUT_DIR", "outputs")
        preview_path = os.path.join(output_dir, filename)
        os.makedirs(output_dir, exist_ok=True)
        
        with open(preview_path, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        print(f"--- POST PUBLISHED SUCCESSFULLY (Simulated) ---")
        print(f"Preview available at: {os.path.abspath(preview_path)}")
        
        return {
            "status": "done",
            "feedback": "Published successfully. Preview created."
        }

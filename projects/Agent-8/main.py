from dotenv import load_dotenv
load_dotenv()

from src.workflow.graph import create_graph

def run():
    print("Initialize Agent-2 System...")
    app = create_graph()
    thread = {"configurable": {"thread_id": "1"}}

    print("Starting Workflow...")
    
    # Initial Run
    # We stream output to see what's happening
    try:
        for event in app.stream({"status": "starting"}, thread, stream_mode="values"):
            # inspect the event/state if needed
            pass
    except Exception as e:
        print(f"Error during execution: {e}")

    # Handle Interrupts
    while True:
        try:
            snapshot = app.get_state(thread)
            if not snapshot.next:
                print("Workflow Completed.")
                break
            
            # We are interrupted
            print("\n--- HUMAN IN THE LOOP REQUIRED ---")
            current_state = snapshot.values
            
            # Determine context based on what's missing or what was just populated
            trend = current_state.get("trend_topic")
            text = current_state.get("post_text")
            image = current_state.get("image_path")
            status = current_state.get("status")
            
            if status == "approving_text":
                # Handle possible unicode print errors in Windows console
                try:
                    print(f"\nGenerated Post Text:\n{text}")
                except UnicodeEncodeError:
                    print(f"\nGenerated Post Text:\n{text.encode('ascii', 'ignore').decode('ascii')}")
                    
                response = input("\nApprove this text? (y/n) [Enter 'y' to approve, 'n' to regenerate, or type specific feedback/edit]: ")
                
                if response.lower() == 'y':
                    print("Text Approved. Proceeding to Image Generation...")
                    # Update status so Planner knows we are moving forward
                    app.update_state(thread, {"status": "approved_text"})
                    for event in app.stream(None, thread, stream_mode="values"): pass
                elif response.lower() == 'n':
                    print("Requesting Regeneration. Sending back to Writer...")
                    app.update_state(thread, {"post_text": "REJECTED"})
                    for event in app.stream(None, thread, stream_mode="values"): pass
                else:
                    print("Updating text with your input...")
                    # If user typed something else, we treat it as an edit
                    app.update_state(thread, {"post_text": "REJECTED", "trend_context": f"{current_state.get('trend_context')}\nUSER EDIT: {response}"})
                    for event in app.stream(None, thread, stream_mode="values"): pass
                    
            elif status == "approving_image":
                print(f"\nGenerated Image Path: {image}")
                
                # Open the image for the human inspector
                import os
                try:
                    os.startfile(image)
                    print("Opening image for review...")
                except Exception as e:
                    print(f"Could not open image automatically: {e}")
                
                response = input("\nApprove this image? (y/n) [Enter 'y' to approve, or 'n' to regenerate]: ")
                
                if response.lower() == 'y':
                    print("Image Approved. Proceeding to Publishing...")
                    app.update_state(thread, {"status": "approved_image"})
                    for event in app.stream(None, thread, stream_mode="values"): pass
                else:
                    print("Requesting Regeneration. Restarting Image generation...")
                    app.update_state(thread, {"image_path": "REJECTED"}) 
                    for event in app.stream(None, thread, stream_mode="values"): pass
                    
            elif status == "error":
                print(f"\nERROR DETECTED IN WORKFLOW: Please check the terminal for the traceback.")
                print(f"Current Memory Context: {current_state}")
                input("Press Enter to forcefully retry, or Ctrl+C to exit...")
                for event in app.stream(None, thread, stream_mode="values"): pass
                
            else:
                # Fallback for unknown interrupt locations
                print(f"\nPaused at unknown state: {status}")
                input("Press Enter to continue...")
                for event in app.stream(None, thread, stream_mode="values"): pass

        except Exception as e:
            print(f"Loop Error: {e}")
            break

if __name__ == "__main__":
    run()

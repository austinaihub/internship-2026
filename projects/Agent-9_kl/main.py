import uuid
from dotenv import load_dotenv
load_dotenv()

from src.workflow.graph import create_graph

def run():
    run_id = str(uuid.uuid4())
    print(f"Initialize Agent-8 System...")
    print(f"Run ID: {run_id}")
    
    app = create_graph()
    thread = {"configurable": {"thread_id": run_id}}

    print("Starting Workflow...")

    # Initial state — Supervisor will route from here
    initial_state = {
        "status": "starting",
        "run_id": run_id,
        "retry_counts": {},
        "messages": [],
    }

    # Initial Run
    try:
        for event in app.stream(initial_state, thread, stream_mode="values"):
            pass
    except Exception as e:
        print(f"Error during execution: {e}")

    # Handle Interrupts (HITL)
    while True:
        try:
            snapshot = app.get_state(thread)
            if not snapshot.next:
                print("Workflow Completed.")
                break

            print("\n--- HUMAN IN THE LOOP REQUIRED ---")
            current_state = snapshot.values

            text   = current_state.get("post_text")
            image  = current_state.get("image_path")
            status = current_state.get("status")

            if status == "approving_text":
                try:
                    print(f"\nGenerated Post Text:\n{text}")
                except UnicodeEncodeError:
                    print(f"\nGenerated Post Text:\n{text.encode('ascii', 'ignore').decode('ascii')}")

                response = input("\nApprove this text? (y/n/feedback): ")

                if response.lower() == 'y':
                    print("Text Approved. Continuing...")
                    app.update_state(thread, {"status": "approved_text"})
                    for event in app.stream(None, thread, stream_mode="values"): pass
                elif response.lower() == 'n':
                    print("Requesting Regeneration...")
                    app.update_state(thread, {"post_text": "REJECTED", "status": "starting"})
                    for event in app.stream(None, thread, stream_mode="values"): pass
                else:
                    print("Updating text with your feedback...")
                    app.update_state(thread, {
                        "post_text": "REJECTED",
                        "trend_context": f"{current_state.get('trend_context')}\nUSER EDIT: {response}",
                        "status": "starting"
                    })
                    for event in app.stream(None, thread, stream_mode="values"): pass

            elif status == "approving_image":
                print(f"\nGenerated Image Path: {image}")
                import os
                try:
                    os.startfile(image)
                    print("Opening image for review...")
                except Exception as e:
                    print(f"Could not open image automatically: {e}")

                response = input("\nApprove this image? (y/n): ")

                if response.lower() == 'y':
                    print("Image Approved. Continuing...")
                    app.update_state(thread, {"status": "approved_image"})
                    for event in app.stream(None, thread, stream_mode="values"): pass
                else:
                    print("Requesting Image Regeneration...")
                    app.update_state(thread, {"image_path": "REJECTED", "status": "starting"})
                    for event in app.stream(None, thread, stream_mode="values"): pass

            elif status == "error":
                print(f"\nERROR IN WORKFLOW. Current state: {current_state}")
                input("Press Enter to retry, or Ctrl+C to exit...")
                for event in app.stream(None, thread, stream_mode="values"): pass

            else:
                print(f"\nPaused at unknown state: {status}")
                input("Press Enter to continue...")
                for event in app.stream(None, thread, stream_mode="values"): pass

        except Exception as e:
            print(f"Loop Error: {e}")
            break

if __name__ == "__main__":
    run()

import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

from src.workflow.graph import create_graph

st.set_page_config(page_title="Agent-8 Control Dashboard", layout="wide")

# Initialize Session State Variables
import datetime
if "thread_id" not in st.session_state:
    # Use exact timestamp as ID to perfectly separate and name each campaign in LangSmith
    st.session_state.thread_id = datetime.datetime.now().strftime("ID-%m%d-%H%M%S")
if "app" not in st.session_state:
    st.session_state.app = create_graph()
if "agent_state" not in st.session_state:
    st.session_state.agent_state = None

st.title("🤖 Agent-8 Multi-Agent System")

# Create Dual Tabs
tab_control, tab_analytics = st.tabs(["🎛️ Control Panel", "📈 LangSmith Analytics"])

with tab_control:
    st.header("Campaign Generator")
    
    # 1. Trigger the workflow
    if st.button("Start Human Trafficking Trend Analysis"):
        st.info("Starting workflow...")
        try:
            # We seed the starting state. 
            # In a real run, this would probably pull from Exa without needing a prior topic, 
            # but we just kick off the graph.
            config = {"configurable": {"thread_id": st.session_state.thread_id}, "run_name": f"Agent-8 Campaign {st.session_state.thread_id}"}
            initial_state = {"status": "starting"}
            
            # Run graph until it hits an interrupt or ends
            for event in st.session_state.app.stream(initial_state, config, stream_mode="values"):
                pass
            
            st.session_state.agent_state = st.session_state.app.get_state(config).values
            st.rerun()
            
        except Exception as e:
            st.error(f"Workflow Error: {e}")

    # 2. Handle Interactive State
    if st.session_state.agent_state:
        current_state = st.session_state.agent_state
        status = current_state.get("status")
        
        st.write("---")
        st.subheader(f"Current System Status: `{status}`")
        
        # --- TREND VISIBILITY ---
        if current_state.get("trend_topic"):
            with st.expander(f"📊 Identified Trend: {current_state.get('trend_topic')}", expanded=False):
                st.write("**Context Summary:**")
                st.write(current_state.get("trend_context", "N/A"))
                
                all_news = current_state.get("all_retrieved_news")
                if all_news:
                    st.write("**All Retrieved Articles from Exa:**")
                    for article in all_news:
                        st.markdown(f"- **{article.get('source')}**: [{article.get('title')}]({article.get('url')})")
                
                raw_news = current_state.get("raw_news")
                if raw_news:
                    st.write("**Specific Sources Cited by AI:**")
                    for article in raw_news:
                        st.markdown(f"- **{article.get('source')}**: [{article.get('title')}]({article.get('url')})")
        
        # --- PROMPT APPROVAL STATE ---
        if status == "approving_prompt":
            st.warning("Action Required: Review AI Writer Instructions")
            current_prompt = current_state.get("writer_prompt", "")
            
            edited_prompt = st.text_area("Writer Prompt:", value=current_prompt, height=250)
            
            if st.button("✅ Approve Prompt & Write Post"):
                config = {"configurable": {"thread_id": st.session_state.thread_id}, "run_name": f"Agent-8 Campaign {st.session_state.thread_id}"}
                st.session_state.app.update_state(config, {"writer_prompt": edited_prompt, "status": "writing"})
                for event in st.session_state.app.stream(None, config, stream_mode="values"): pass
                st.session_state.agent_state = st.session_state.app.get_state(config).values
                st.rerun()

        # --- TEXT APPROVAL STATE ---
        elif status == "approving_text":
            st.warning("Action Required: Review Drafted Text")
            draft_text = current_state.get("post_text")
            
            st.text_area("Generated Post:", value=draft_text, height=200, disabled=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Approve Text"):
                    config = {"configurable": {"thread_id": st.session_state.thread_id}, "run_name": f"Agent-8 Campaign {st.session_state.thread_id}"}
                    st.session_state.app.update_state(config, {"status": "approved_text"})
                    for event in st.session_state.app.stream(None, config, stream_mode="values"): pass
                    st.session_state.agent_state = st.session_state.app.get_state(config).values
                    st.rerun()
            with col2:
                if st.button("🔄 Reject & Regenerate"):
                    config = {"configurable": {"thread_id": st.session_state.thread_id}, "run_name": f"Agent-8 Campaign {st.session_state.thread_id}"}
                    st.session_state.app.update_state(config, {"post_text": "REJECTED"})
                    for event in st.session_state.app.stream(None, config, stream_mode="values"): pass
                    st.session_state.agent_state = st.session_state.app.get_state(config).values
                    st.rerun()
            
            with col3:
                custom_edit = st.text_input("Or apply custom edit:")
                if st.button("Apply Edit") and custom_edit:
                    config = {"configurable": {"thread_id": st.session_state.thread_id}, "run_name": f"Agent-8 Campaign {st.session_state.thread_id}"}
                    st.session_state.app.update_state(config, {
                        "post_text": "REJECTED", 
                        "trend_context": f"{current_state.get('trend_context')}\nUSER EDIT: {custom_edit}"
                    })
                    for event in st.session_state.app.stream(None, config, stream_mode="values"): pass
                    st.session_state.agent_state = st.session_state.app.get_state(config).values
                    st.rerun()

        # --- IMAGE APPROVAL STATE ---
        elif status == "approving_image":
            st.warning("Action Required: Review Generated Image")
            image_path = current_state.get("image_path")
            
            if image_path and os.path.exists(image_path):
                st.image(image_path, caption="Generated Visual", use_container_width=True)
            else:
                st.error("Image file not found.")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve Image & Publish"):
                    config = {"configurable": {"thread_id": st.session_state.thread_id}, "run_name": f"Agent-8 Campaign {st.session_state.thread_id}"}
                    st.session_state.app.update_state(config, {"status": "publisher"})
                    for event in st.session_state.app.stream(None, config, stream_mode="values"): pass
                    st.session_state.agent_state = st.session_state.app.get_state(config).values
                    st.rerun()
            with col2:
                image_feedback = st.text_input("Critique/Feedback (optional):")
                if st.button("🔄 Regenerate Image with Feedback"):
                    config = {"configurable": {"thread_id": st.session_state.thread_id}, "run_name": f"Agent-8 Campaign {st.session_state.thread_id}"}
                    st.session_state.app.update_state(config, {
                        "image_path": "REJECTED",
                        "image_feedback": image_feedback
                    })
                    for event in st.session_state.app.stream(None, config, stream_mode="values"): pass
                    st.session_state.agent_state = st.session_state.app.get_state(config).values
                    st.rerun()
                    
        elif status == "done": # Assuming final published state.
            st.success("🎉 Campaign Successfully Published!")
            
            with st.container(border=True):
                st.markdown("### 📱 Final Social Media Post")
                if current_state.get("image_path") and os.path.exists(current_state.get("image_path")):
                    st.image(current_state.get("image_path"), use_container_width=True)
                st.write(current_state.get("post_text"))
            
            if st.button("Start New Campaign"):
                 st.session_state.thread_id = datetime.datetime.now().strftime("ID-%m%d-%H%M%S")
                 st.session_state.agent_state = None
                 st.rerun()

        elif status == "error":
             st.error("Workflow encountered a terminal error.")
             st.write(current_state.get("feedback"))
             
        elif status not in ["approving_prompt", "approving_text", "approving_image", "error", "done"]:
            with st.spinner(f"Agent working on {status}..."):
                config = {"configurable": {"thread_id": st.session_state.thread_id}, "run_name": f"Agent-8 Campaign {st.session_state.thread_id}"}
                for event in st.session_state.app.stream(None, config, stream_mode="values"): pass
                st.session_state.agent_state = st.session_state.app.get_state(config).values
                st.rerun()

with tab_analytics:
    st.header("LangSmith Operation Metrics")
    st.write("Live telemetry fetching from LangSmith API...")
    
    try:
        from langsmith import Client
        client = Client()
        
        # We attempt to pull the most recent runs from the project
        project_name = os.getenv("LANGCHAIN_PROJECT", "Agent-7-Observability")
        
        # Fetch the last 5 root runs
        runs = list(client.list_runs(
            project_name=project_name,
            execution_order=1, # Only get root runs (traces)
            limit=5
        ))
        
        if not runs:
            st.info("No LangSmith runs found for this project yet. Start a campaign in the Control Panel!")
        else:
            # Prepare data for the table
            metrics_data = []
            
            for run in runs:
                # Calculate latency
                latency_s = 0.0
                if run.end_time and run.start_time:
                    latency_s = (run.end_time - run.start_time).total_seconds()
                
                # Extract Token Usage & Cost (If available in the trace)
                tokens = run.prompt_tokens + run.completion_tokens if run.prompt_tokens else 0
                cost = getattr(run, "total_cost", 0.0) or 0.0
                
                metrics_data.append({
                    "Run ID": str(run.id)[:8],
                    "Name": run.name,
                    "Start Time": run.start_time.strftime("%H:%M:%S") if run.start_time else "N/A",
                    "Latency (s)": round(latency_s, 2),
                    "Total Tokens": tokens,
                    "Estimated Cost ($)": f"${cost:.4f}",
                    "Status": "Success" if run.error is None else "Error"
                })
                
            # Display High Level KPIs for the absolute most recent run
            st.subheader("Latest Execution KPIs")
            latest = metrics_data[0]
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Latency", f"{latest['Latency (s)']}s")
            col2.metric("Total Tokens", latest['Total Tokens'])
            col3.metric("Estimated Cost", latest['Estimated Cost ($)'])
            col4.metric("Status", latest['Status'])
            
            st.write("---")
            st.subheader("Recent Campaign Executions")
            
            # Fetch a larger pool of runs to group by campaign thread
            # Fetch a larger pool of runs using a generator to avoid API limits
            # and ensure we skip internal noise runs
            runs = []
            try:
                run_generator = client.list_runs(
                    project_name=project_name,
                    execution_order=1
                )
                
                for run in run_generator:
                    if getattr(run, "name", "") == "LangGraphUpdateState" or run.name.startswith("__"):
                        continue
                        
                    runs.append(run)
                    if len(runs) >= 50:  # Grab the 50 freshest valid campaigns
                        break
            except Exception as e:
                st.error(f"Error fetching runs: {e}")
            
            # Sort explicitly by start_time descending to ensure freshest runs are processed first
            runs.sort(key=lambda x: x.start_time if x.start_time else getattr(x, 'end_time', None), reverse=True)
            
            # Group runs by thread_id
            campaigns = {}
            for run in runs:
                metadata = run.extra.get('metadata', {}) if run.extra else {}
                thread_id = metadata.get('thread_id', 'unknown')
                
                # Filter out pure test runs or unknown threads if desired, but we'll include them
                if thread_id not in campaigns:
                    campaigns[thread_id] = {
                        "runs": [],
                        "start_time": run.start_time,
                        "total_latency": 0.0,
                        "total_tokens": 0,
                        "total_cost": 0.0
                    }
                
                campaigns[thread_id]["runs"].append(run)
                
                if run.end_time and run.start_time:
                    campaigns[thread_id]["total_latency"] += (run.end_time - run.start_time).total_seconds()
                
                tokens = run.prompt_tokens + run.completion_tokens if run.prompt_tokens else 0
                campaigns[thread_id]["total_tokens"] += tokens
                campaigns[thread_id]["total_cost"] += float(getattr(run, "total_cost", 0.0) or 0.0)
                
                # Earliest start time is the true start
                if run.start_time and run.start_time < campaigns[thread_id]["start_time"]:
                    campaigns[thread_id]["start_time"] = run.start_time

            sorted_threads = sorted(campaigns.keys(), key=lambda t: campaigns[t]["start_time"], reverse=True)
            
            for thread_id in sorted_threads:
                camp = campaigns[thread_id]
                run_time = camp["start_time"].strftime("%m/%d %H:%M:%S") if camp["start_time"] else "N/A"
                expander_title = f"🚀 Campaign Thread {thread_id} | Started: {run_time} | {round(camp['total_latency'], 2)}s | {camp['total_tokens']} tokens | ${camp['total_cost']:.4f}"
                
                with st.expander(expander_title):
                    st.write(f"**Campaign Thread ID:** `{thread_id}`")
                    
                    # Sort the execution steps (root runs) within this campaign
                    sorted_root_runs = sorted(camp["runs"], key=lambda x: x.start_time if x.start_time else getattr(x, 'end_time', None))
                    
                    for root_run in sorted_root_runs:
                        # Calculate step latency and tokens
                        step_latency_s = 0.0
                        if root_run.end_time and root_run.start_time:
                            step_latency_s = (root_run.end_time - root_run.start_time).total_seconds()
                            
                        step_tokens = root_run.prompt_tokens + root_run.completion_tokens if root_run.prompt_tokens else 0
                        step_cost = float(getattr(root_run, "total_cost", 0.0) or 0.0)
                        
                        step_time = root_run.start_time.strftime("%H:%M:%S") if root_run.start_time else "N/A"
                        step_title = f"📦 Execution Step at {step_time} ({round(step_latency_s, 2)}s | {step_tokens} tokens | ${step_cost:.4f})"
                        
                        with st.expander(step_title):
                            try:
                                child_runs = list(client.list_runs(
                                    project_name=project_name,
                                    trace_id=str(root_run.id)
                                ))
                            except Exception:
                                child_runs = []
                                
                            # Sort all child runs chronologically
                            child_runs.sort(key=lambda x: x.start_time if x.start_time else getattr(x, 'end_time', None))
                            
                            for crun in child_runs:
                                if str(crun.id) == str(root_run.id):
                                    continue # Skip the root itself
                                    
                                c_prompt_tokens = crun.prompt_tokens or 0
                                c_comp_tokens = crun.completion_tokens or 0
                                c_tokens = c_prompt_tokens + c_comp_tokens
                                c_latency_s = 0.0
                                if crun.end_time and crun.start_time:
                                    c_latency_s = (crun.end_time - crun.start_time).total_seconds()
                                    
                                if c_tokens == 0 and c_latency_s < 0.1 and crun.name.startswith("__"):
                                    continue
    
                                c_cost = float(getattr(crun, "total_cost", 0.0) or 0.0)
                                run_type_icon = "🧠" if "llm" in getattr(crun, 'run_type', '').lower() else "⚙️"
                                
                                with st.expander(f"{run_type_icon} {crun.name} ({round(c_latency_s, 2)}s | {c_tokens} tokens | ${c_cost:.4f})"):
                                    c1, c2, c3, c4 = st.columns(4)
                                    c1.metric("Latency", f"{round(c_latency_s, 2)}s")
                                    c2.metric("Prompt Tokens", c_prompt_tokens)
                                    c3.metric("Completion Tokens", c_comp_tokens)
                                    c4.metric("Cost", f"${c_cost:.4f}")
                                    
                                    st.markdown("**Inputs:**")
                                    st.json(crun.inputs or {})
                                    
                                    st.markdown("**Outputs:**")
                                    st.json(crun.outputs or {})
            
            if st.button("Refresh Telemetry"):
                st.rerun()

    except Exception as e:
        st.error(f"Failed to connect to LangSmith: {e}")
        st.write("Please ensure `LANGCHAIN_API_KEY` is set in your `.env` file.")

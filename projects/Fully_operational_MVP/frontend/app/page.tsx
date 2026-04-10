"use client";

import { useState, useEffect } from "react";
import { CheckCircle2, XCircle, Search, RefreshCw, Send, LayoutDashboard, Link2, FileText, Image as ImageIcon, Loader2, PenTool, Sparkles, UserCheck } from "lucide-react";

export default function Home() {
  const [threadId, setThreadId] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [tuningInstruction, setTuningInstruction] = useState("");
  const [agentState, setAgentState] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const API_BASE = "http://localhost:8002/api/workflow";

  const fetchState = async (tid: string) => {
    try {
      const res = await fetch(`${API_BASE}/${tid}/state`);
      if (res.ok) {
        const data = await res.json();
        setAgentState(data.state);
        setLoading(false);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (threadId) {
      interval = setInterval(() => {
        fetchState(threadId);
      }, 2000); // Poll every 2s
    }
    return () => clearInterval(interval);
  }, [threadId]);

  const startWorkflow = async () => {
    setLoading(true);
    setAgentState(null);
    try {
      const res = await fetch(`${API_BASE}/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ manual_url: urlInput }),
      });
      const data = await res.json();
      setThreadId(data.thread_id);
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  const submitFeedback = async (updates: any) => {
    setLoading(true);
    try {
      await fetch(`${API_BASE}/${threadId}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ state_updates: updates }),
      });
      setTuningInstruction(""); // clear input
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  const status = agentState?.status || "idle";

  return (
    <div className="min-h-screen flex flex-col font-sans">
      {/* Edge-to-Edge Cybernetic Header */}
      <header className="w-full border-b border-zinc-800/80 bg-black/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-2 border border-purple-500/30 bg-purple-500/10 rounded-md shadow-[0_0_15px_rgba(139,92,246,0.15)] flex items-center justify-center">
              <LayoutDashboard className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-wide text-white flex items-center gap-3">
                <img src="/logo.jpg" alt="Austin AI Hub Logo" className="w-8 h-8 rounded-full border border-cyan-500/50 shadow-[0_0_10px_rgba(6,182,212,0.3)] object-cover" />
                <span className="flex items-center">
                  AUSTIN<span className="text-cyan-400">AI</span>HUB
                </span>
                <span className="text-zinc-600 font-normal px-1">|</span> 
                <span className="text-zinc-300 font-mono text-sm tracking-widest font-normal">CONTENT CREATOR</span>
              </h1>
            </div>
          </div>
          <div>
            {status !== "idle" && (
              <div className={`px-4 py-1.5 rounded-md font-mono text-xs tracking-wider uppercase border flex items-center gap-2 ${loading ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-400 shadow-[0_0_10px_rgba(6,182,212,0.2)]' : 'border-zinc-700 bg-black/50 text-zinc-400'}`}>
                {loading && <RefreshCw className="w-3 h-3 animate-spin" />}
                SYS.STATE: {status.replace('_', ' ')}
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1 w-full max-w-[1600px] mx-auto p-6 lg:p-8 flex flex-col gap-8">

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Input & Sidebar */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          <div className="glass-panel p-6 flex flex-col gap-5">
            <h2 className="text-xs font-mono font-bold tracking-widest text-zinc-400 uppercase flex items-center gap-2 border-b border-zinc-800 pb-3">
              <Link2 className="w-4 h-4"/> Input Parameter
            </h2>
            <div className="relative">
              <div className="absolute top-0 left-0 h-full w-[2px] bg-cyan-500/50 rounded-l-md shadow-[0_0_10px_rgba(6,182,212,0.5)]"></div>
              <input 
                type="text" 
                placeholder="Target URL (Leave blank for autonomous scan)..."
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                disabled={status !== "idle" && status !== "done"}
                className="pl-4 font-mono text-sm"
              />
            </div>
            <button 
              className="btn-primary w-full flex justify-center items-center gap-2 mt-2"
              onClick={startWorkflow}
              disabled={status !== "idle" && status !== "done" && status !== "error"}
            >
              <Search className="w-4 h-4" /> 
              INITIATE SCAN
            </button>
          </div>

          {agentState?.all_retrieved_news && (
            <div className="glass-panel p-0 flex flex-col flex-grow overflow-hidden">
              <h2 className="text-xs font-mono font-bold tracking-widest text-cyan-400 uppercase flex items-center gap-2 border-b border-zinc-800 bg-cyan-900/10 p-4">
                Intercepted Intel Streams
              </h2>
              <div className="flex flex-col overflow-y-auto max-h-[500px]">
                {agentState.all_retrieved_news.map((news: any, idx: number) => (
                  <a key={idx} href={news.url} target="_blank" rel="noreferrer" className="p-4 border-b border-zinc-800/50 hover:bg-white/5 transition-colors block group relative">
                    <div className="absolute left-0 top-0 h-full w-[2px] bg-transparent group-hover:bg-cyan-500 transition-colors"></div>
                    <span className="font-mono text-xs text-cyan-500/80 block mb-2 tracking-wide uppercase">{news.source}</span>
                    <span className="text-zinc-300 text-sm leading-snug line-clamp-2 font-medium">{news.title}</span>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Dynamic Agent Actions */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          {!agentState && !loading ? (
            <div className="glass-panel h-full min-h-[400px] flex flex-col items-center justify-center p-12 text-center text-zinc-600 border border-zinc-800">
              <Search className="w-10 h-10 mb-4 opacity-30" />
              <h3 className="text-lg font-mono font-medium text-zinc-500 uppercase tracking-widest">System Standby</h3>
              <p className="text-sm mt-2 max-w-sm">Awaiting manual URL input or autonomous deployment signal.</p>
            </div>
          ) : (
            <>
              {/* Dynamic Status Animation Bar */}
              <div className="glass-panel p-4 flex items-center justify-center gap-6 bg-black/40 border border-purple-500/20 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-purple-500/50 to-transparent"></div>
                {((!agentState && loading) || status === "starting" || status === "trend_analyzer") && (
                  <div className="flex items-center gap-3 text-purple-400 font-mono text-sm tracking-widest uppercase">
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span className="animate-pulse">Accessing Web Nodes...</span>
                  </div>
                )}
                {status === "writing" && (
                  <div className="flex items-center gap-3 text-cyan-400 font-mono text-sm tracking-widest uppercase">
                    <PenTool className="w-5 h-5 animate-pulse" />
                    <span>Synthesizing Narrative...</span>
                  </div>
                )}
                {(status === "generating_image" || status === "image_generator") && (
                  <div className="flex items-center gap-3 text-emerald-400 font-mono text-sm tracking-widest uppercase">
                    <Sparkles className="w-5 h-5 animate-spin" />
                    <span className="animate-pulse">Rendering Visuals (Nano Banana)...</span>
                  </div>
                )}
                {status.includes("approving") && (
                  <div className="flex items-center gap-3 text-amber-500 font-mono text-sm tracking-widest uppercase">
                    <UserCheck className="w-5 h-5 animate-pulse" />
                    <span>Awaiting Operator Override...</span>
                  </div>
                )}
                {(status === "done" || status === "publisher") && (
                  <div className="flex items-center gap-3 text-zinc-500 font-mono text-sm tracking-widest uppercase">
                    <CheckCircle2 className="w-5 h-5" />
                    <span>Operation Terminated</span>
                  </div>
                )}
              </div>

              {/* Trend Approval Step */}
              {agentState?.trend_topic && (
                <div className={`glass-panel p-6 ${status === "approving_prompt" ? "ring-2 ring-purple-500/50 shadow-[0_0_15px_rgba(139,92,246,0.15)]" : "opacity-70"}`}>
                  <h2 className="text-xl font-semibold mb-2 flex items-center gap-2">
                    <Search className="text-purple-400 w-5 h-5"/> Discovered Trend
                  </h2>
                  <div className="text-xl font-medium text-white mb-4 bg-zinc-900 p-4 rounded-lg border border-zinc-800">
                    {agentState.trend_topic}
                  </div>
                  
                  {status === "approving_prompt" && (
                    <div className="mt-6 flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-4">
                      <div className="bg-zinc-900 border border-zinc-800 p-4 rounded-lg">
                        <p className="text-sm text-zinc-400 mb-2 font-medium">Writer Agent Prompt Draft:</p>
                        <textarea 
                          className="h-32" 
                          value={tuningInstruction || agentState.writer_prompt}
                          onChange={(e) => setTuningInstruction(e.target.value)}
                        />
                      </div>
                      <div className="flex gap-4">
                        <button className="btn-accept flex-1 flex items-center justify-center gap-2" onClick={() => submitFeedback({status: "writing", writer_prompt: tuningInstruction || agentState.writer_prompt})}>
                          <CheckCircle2 className="w-5 h-5" /> Accept & Generate Text
                        </button>
                        <button className="btn-reject flex items-center gap-2" onClick={() => submitFeedback({status: "starting", trend_topic: null})}>
                          <XCircle className="w-5 h-5" /> Reject Trend
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Image Approval Step */}
              {agentState?.image_path && agentState.image_path !== "REJECTED" && status !== "done" && (
                <div className={`glass-panel p-6 ${status === "approving_image" ? "ring-2 ring-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.15)]" : "opacity-70"}`}>
                  <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                    <ImageIcon className="text-emerald-400 w-5 h-5"/> Visual Asset
                  </h2>
                  <div className="flex justify-center bg-black/50 p-4 rounded-lg border border-zinc-800 overflow-hidden">
                    <img src={agentState.image_path} alt="Generated Asset" className="max-w-full rounded-md object-contain max-h-[400px]" onError={(e) => (e.currentTarget.style.display = 'none')} />
                  </div>
                  
                  {status === "approving_image" && (
                    <div className="mt-6 flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-4">
                      <div>
                        <p className="text-sm text-zinc-400 mb-2 font-medium">Tuning Instructions for Regeneration (if rejecting):</p>
                        <input 
                          type="text" 
                          placeholder="Remove text from image, make it abstract..."
                          value={tuningInstruction}
                          onChange={(e) => setTuningInstruction(e.target.value)}
                        />
                      </div>
                      <div className="flex gap-4">
                        <button className="btn-accept flex-1 flex items-center justify-center gap-2" onClick={() => submitFeedback({status: "publisher"})}>
                          <Send className="w-5 h-5" /> Accept & Publish
                        </button>
                        <button className="btn-reject flex items-center gap-2 px-6" onClick={() => submitFeedback({image_path: "REJECTED", image_feedback: tuningInstruction})}>
                          <RefreshCw className="w-5 h-5" /> Reject & Regenerate
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Text Approval Step */}
              {agentState?.post_text && agentState.post_text !== "REJECTED" && status !== "done" && (
                <div className={`glass-panel p-6 ${status === "approving_text" ? "ring-2 ring-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.15)]" : "opacity-70"}`}>
                  <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                    <FileText className="text-blue-400 w-5 h-5"/> Generated Brief
                  </h2>
                  <div className="text-zinc-300 leading-relaxed bg-zinc-900 p-6 rounded-lg border border-zinc-800 whitespace-pre-wrap">
                    {agentState.post_text}
                  </div>
                  
                  {status === "approving_text" && (
                    <div className="mt-6 flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-4">
                       <div>
                        <p className="text-sm text-zinc-400 mb-2 font-medium">Tuning Instructions for Rewrite (if rejecting):</p>
                        <input 
                          type="text" 
                          placeholder="Make it shorter and more professional..."
                          value={tuningInstruction}
                          onChange={(e) => setTuningInstruction(e.target.value)}
                        />
                      </div>
                      <div className="flex gap-4">
                        <button className="btn-accept flex-1 flex items-center justify-center gap-2" onClick={() => submitFeedback({status: "approved_text"})}>
                          <CheckCircle2 className="w-5 h-5" /> Accept Text
                        </button>
                        <button className="btn-reject flex items-center gap-2 px-6" onClick={() => submitFeedback({post_text: "REJECTED", trend_context: agentState.trend_context + "\nUSER EDIT: " + tuningInstruction})}>
                          <RefreshCw className="w-5 h-5" /> Reject & Rewrite
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Final State - Unified Publisher Display */}
              {status === "done" && (
                <div className="flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-6">
                  <div className="glass-panel p-8 text-center bg-gradient-to-t from-emerald-900/20 to-transparent border-emerald-900/50">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/20 text-emerald-400 mb-4 shadow-[0_0_15px_rgba(16,185,129,0.4)]">
                      <CheckCircle2 className="w-8 h-8" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">Campaign Published</h2>
                    <p className="text-zinc-400 mb-6">The intelligence brief and visual asset have been successfully distributed.</p>
                    <button className="btn-primary" onClick={() => {setAgentState(null); setThreadId("");}}>Start New Investigation</button>
                  </div>
                  
                  {/* Unified Content Frame */}
                  <div className="glass-panel p-0 overflow-hidden border border-emerald-500/30 shadow-[0_0_30px_rgba(16,185,129,0.15)]">
                    {/* 1. Image Rendered ABOVE Text */}
                    {agentState.image_path && (
                      <div className="w-full bg-black/90 flex justify-center border-b border-zinc-800">
                        <img src={agentState.image_path} alt="Generated Asset" className="w-full object-contain max-h-[500px]" onError={(e) => (e.currentTarget.style.display = 'none')} />
                      </div>
                    )}
                    
                    {/* 2. Text Rendered BELOW Image */}
                    {agentState.post_text && (
                      <div className="p-8 bg-zinc-900/95">
                        <h3 className="text-lg font-semibold text-emerald-400 mb-4 flex items-center gap-2">
                          <Send className="w-5 h-5" /> Live Post Content
                        </h3>
                        <div className="text-zinc-300 leading-relaxed whitespace-pre-wrap text-[15px]">
                          {agentState.post_text}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

            </>
          )}
        </div>
      </div>
    </main>
  </div>
  );
}

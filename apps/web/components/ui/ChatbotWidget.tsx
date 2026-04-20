"use client";

import React, { useRef, useState, useEffect } from "react";
import { Bot, X, Send, ImagePlus, Loader2, CheckCircle2, Sparkles, ArrowRight } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { useNGOAuth } from "@/lib/ngo-auth";
import { usePathname, useRouter } from "next/navigation";
import { api } from "@/lib/ngo-api";

type Message = {
  id: string;
  role: "user" | "bot";
  text: string;
  imageUrl?: string;
  statusLog?: string[];
  isSuccess?: boolean;
};

export function ChatbotWidget() {
  const { user, loading: authLoading } = useNGOAuth();
  const pathname = usePathname();
  const router = useRouter();

  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { 
      id: "0", 
      role: "bot", 
      text: "Namaste! I'm Saathi, your autonomous resolution assistant. Whether you're an NGO or a volunteer, I'm here to do the heavy lifting for you. How can I help today?" 
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [activeTasks, setActiveTasks] = useState<any[]>([]);
  
  const fileRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Sync active tasks context if on relevant pages
  useEffect(() => {
    if (open && user && user.role === "volunteer") {
      api.volTasks(user.token).then(setActiveTasks).catch(() => {});
    }
  }, [open, user]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open, executing]);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    const reader = new FileReader();
    reader.onload = () => setImagePreview(reader.result as string);
    reader.readAsDataURL(file);
    e.target.value = "";
  };

  const clearImage = () => {
    setImageFile(null);
    setImagePreview(null);
  };

  const runCalls = async (calls: any[]) => {
    if (!calls || calls.length === 0 || !user) return [];
    const logs: string[] = [];
    
    for (const call of calls) {
      const { method, args = [] } = call;
      const methodName = method.replace("api.", "");
      // @ts-ignore
      const apiFn = api[methodName];
      
      if (typeof apiFn === "function") {
        setExecuting(`${methodName.replace(/([A-Z])/g, ' $1').toLowerCase()}...`);
        try {
          await apiFn(user.token, ...args);
          logs.push(`✅ ${methodName.replace(/([A-Z])/g, ' $1').toLowerCase()} completed`);
        } catch (err: any) {
          logs.push(`❌ ${methodName} failed: ${err.message}`);
        }
      }
    }
    setExecuting(null);
    return logs;
  };

  const send = async () => {
    if (!input.trim() && !imageFile) return;
    if (loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      text: input.trim() || (imageFile ? "I'm uploading this to verify my task progress." : ""),
      imageUrl: imagePreview ?? undefined,
    };
    
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    let imageBase64: string | undefined;
    let imageMimeType: string | undefined;

    if (imageFile) {
      const buffer = await imageFile.arrayBuffer();
      const bytes = new Uint8Array(buffer);
      let binary = "";
      bytes.forEach((b) => (binary += String.fromCharCode(b)));
      imageBase64 = btoa(binary);
      imageMimeType = imageFile.type;
    }

    clearImage();

    try {
      const res = await fetch("/api/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: userMsg.text, 
          imageBase64, 
          imageMimeType,
          context: {
            role: user?.role,
            userName: user?.email.split('@')[0],
            page: pathname,
            activeTasks: activeTasks.length > 0 ? activeTasks : undefined
          }
        }),
      });
      
      const data = await res.json();
      const logs = await runCalls(data.calls || []);
      
      if (data.action?.type === "navigate" && data.action.path) {
        setTimeout(() => router.push(data.action.path), 1200);
      }

      setMessages((prev) => [
        ...prev,
        { 
          id: (Date.now() + 1).toString(), 
          role: "bot", 
          text: data.reply ?? data.error ?? "Resolution complete.",
          statusLog: logs.length > 0 ? logs : undefined,
          isSuccess: data.action?.task_resolved || data.action?.type === "resolve_task"
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { id: Date.now().toString(), role: "bot", text: "Connection error. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <motion.button
        onClick={() => setOpen((v) => !v)}
        whileHover={{ scale: 1.1, rotate: 5 }}
        whileTap={{ scale: 0.9 }}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-2xl shadow-2xl flex items-center justify-center overflow-hidden transition-all"
        style={{ background: "linear-gradient(135deg, #115E54 0%, #2A8256 100%)", boxShadow: "0 8px 32px rgba(17, 94, 84, 0.4)" }}
      >
        <AnimatePresence mode="wait">
          {open ? <X size={24} className="text-white" key="x" /> : <Bot size={24} className="text-white" key="bot" />}
        </AnimatePresence>
      </motion.button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 32, scale: 0.9, filter: "blur(10px)" }}
            animate={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: 32, scale: 0.9, filter: "blur(10px)" }}
            className="fixed bottom-24 right-6 z-50 w-[350px] flex flex-col rounded-3xl shadow-2xl overflow-hidden border"
            style={{ height: "550px", borderColor: "rgba(255, 255, 255, 0.1)", background: "rgba(255, 255, 255, 0.8)", backdropFilter: "blur(20px)" }}
          >
            <div className="px-5 py-4 shrink-0 flex items-center justify-between" style={{ background: "linear-gradient(135deg, #115E54 0%, #2A8256 100%)" }}>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center backdrop-blur-md border border-white/30">
                  <Bot size={20} className="text-white" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white tracking-tight">Saathi Resolution</h3>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-[10px] text-white/70 font-medium">Autonomous Intelligence</span>
                  </div>
                </div>
              </div>
              <button onClick={() => setOpen(false)} className="w-8 h-8 rounded-full flex items-center justify-center hover:bg-white/10">
                <X size={16} className="text-white/60" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6 custom-scrollbar">
              {messages.map((m) => (
                <div key={m.id} className={`flex flex-col ${m.role === "user" ? "items-end" : "items-start"}`}>
                  <motion.div
                    initial={{ opacity: 0, x: m.role === "user" ? 10 : -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className={`max-w-[85%] rounded-3xl px-4 py-3 text-[13px] leading-relaxed shadow-sm ${m.role === "user" ? "rounded-tr-none text-white" : "rounded-tl-none border"}`}
                    style={m.role === "user" ? { background: "linear-gradient(135deg, #115E54 0%, #2A8256 100%)" } : { background: "white", color: "#1e293b", borderColor: "#f1f5f9" }}
                  >
                    {m.imageUrl && <img src={m.imageUrl} alt="upload" className="rounded-2xl mb-3 max-h-40 w-full object-cover border border-white/10" />}
                    <div dangerouslySetInnerHTML={{ __html: m.text }} />
                    {m.statusLog && (
                      <div className="mt-3 pt-3 border-t border-slate-100 space-y-1">
                        {m.statusLog.map((log, i) => (
                          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.2 }} key={i} className="text-[10px] font-medium text-emerald-600 flex items-center gap-1.5">{log}</motion.p>
                        ))}
                      </div>
                    )}
                    {m.isSuccess && (
                      <div className="mt-3 p-2 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center"><CheckCircle2 size={12} className="text-white" /></div>
                        <span className="text-[10px] font-bold text-emerald-700">RESOLVED</span>
                        <Sparkles size={12} className="text-emerald-400 ml-auto animate-bounce" />
                      </div>
                    )}
                  </motion.div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-white border border-slate-100 rounded-3xl rounded-tl-none px-4 py-4 flex flex-col gap-3 shadow-sm">
                    <div className="flex items-center gap-3">
                      <div className="flex gap-1">
                        <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 1 }} className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 1, delay: 0.2 }} className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 1, delay: 0.4 }} className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                      </div>
                      <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">Saathi is thinking</span>
                    </div>
                    {executing && (
                      <div className="flex items-center gap-2 px-2 py-1.5 rounded-xl bg-slate-50 border border-slate-100">
                        <Loader2 size={10} className="animate-spin text-emerald-600" />
                        <span className="text-[10px] font-medium text-slate-500 italic">{executing}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            <div className="p-4 bg-white/50 border-t border-slate-100 space-y-3">
              {imagePreview && (
                <div className="relative inline-block group">
                  <img src={imagePreview} alt="preview" className="h-20 w-20 rounded-2xl object-cover border-2 border-emerald-500 shadow-lg" />
                  <button onClick={clearImage} className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-rose-500 text-white flex items-center justify-center shadow-lg hover:bg-rose-600"><X size={12} /></button>
                </div>
              )}
              <div className="flex items-end gap-2.5">
                <input type="file" accept="image/*" ref={fileRef} className="hidden" onChange={handleImageSelect} />
                <button onClick={() => fileRef.current?.click()} className="w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 border border-slate-200 bg-white hover:border-emerald-500 hover:text-emerald-600 shadow-sm"><ImagePlus size={18} /></button>
                <div className="flex-1">
                  <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
                    placeholder="Ask Saathi to act..."
                    rows={1}
                    className="w-full resize-none rounded-2xl px-4 py-3 text-[13px] outline-none border border-slate-200 focus:border-emerald-500 transition-all"
                    style={{ maxHeight: "120px", background: "white" }}
                  />
                </div>
                <motion.button onClick={send} disabled={loading || (!input.trim() && !imageFile)} whileHover={{ scale: 1.05 }} className="w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 shadow-lg" style={{ background: "linear-gradient(135deg, #115E54 0%, #2A8256 100%)" }}><ArrowRight size={18} className="text-white" /></motion.button>
              </div>
              <p className="text-[9px] text-center text-slate-400 font-medium font-mono">SAATHI • DEPLOYED MODE</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

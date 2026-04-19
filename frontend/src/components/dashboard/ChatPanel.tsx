import { ArrowRight } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useAppStore } from "../../store/appStore";

export function ChatPanel() {
  const [input, setInput] = useState("");
  const { messages, appendMessage, sendMessage, metrics } = useAppStore();

  const handleSend = () => {
    if (!input.trim()) return;
    
    // Optimistically update the UI with user message
    appendMessage({
      id: `#0${messages.length + 2}`,
      tokens: `↑ ${Math.floor(input.length * 0.25)} tok`,
      text: input,
      isUser: true
    });
    
    // Broadcast across socket
    sendMessage(input);
    setInput("");
  };

  const endRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  return (
    <section className={`min-w-[320px] flex flex-col border-r border-surface-dim bg-white h-full relative cursor-default flex-1 w-full`}>
      <div className="px-6 py-5 flex justify-between items-center border-b border-surface-dim bg-background">
        <div className="flex flex-col gap-1">
          <span className="font-sans font-black text-black text-2xl tracking-tighter uppercase">
            CCM
          </span>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-black border border-black animate-pulse"></span>
            <span className="font-sans font-bold text-[9px] text-black tracking-[0.2em] uppercase">
              COMPRESSING... {Math.round(metrics.compRatio * 100)}% reduction
            </span>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className="flex items-center gap-2 bg-white border border-surface-dim px-2 py-1 font-bold text-[10px] text-ink">
            <span>{metrics.compressed_tokens.toLocaleString()} / {metrics.raw_tokens.toLocaleString()}</span>
            <div className="w-12 h-2 bg-surface-dim overflow-hidden">
              <div 
                className="h-full bg-ink transition-all duration-500" 
                style={{ width: `${metrics.raw_tokens > 0 ? (metrics.compressed_tokens / metrics.raw_tokens) * 100 : 0}%` }} 
              ></div>
            </div>
          </div>
          <span className="px-2 py-0.5 bg-ink text-surface text-[9px] font-bold uppercase tracking-widest">
            VRAM: {(metrics.vram_mb / 1024).toFixed(1)}GB
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-8 flex flex-col gap-8 no-scrollbar bg-white">
        {messages.map((msg, idx) => (
          msg.isUser ? (
            <div key={idx} className="flex flex-col gap-2 max-w-[90%] self-end items-end text-right">
              <div className="flex items-center gap-2 font-bold text-[10px] text-[#888] uppercase tracking-widest">
                <span className="text-ink">{msg.tokens}</span>
                <span className="bg-white border border-surface-dim px-1 text-ink">{msg.id}</span>
              </div>
              <div className="bg-white border border-surface-dim p-5 border-r-[4px] shadow-sm">
                <p className="text-sm leading-relaxed text-ink font-bold">
                  {msg.text}
                </p>
              </div>
            </div>
          ) : (
            <div key={idx} className="flex flex-col gap-2 max-w-[90%]">
              <div className="flex items-center gap-2 font-bold text-[10px] text-[#888] uppercase tracking-widest">
                <span className="bg-background border border-surface-dim px-1 text-ink">{msg.id}</span>
                <span>{msg.tokens}</span>
              </div>
              <div className="bg-background p-5 border border-surface-dim border-l-[4px] shadow-sm">
                <p className="text-sm leading-relaxed text-ink font-medium">
                  {msg.text}
                </p>
              </div>
            </div>
          )
        ))}
        <div ref={endRef} />
      </div>

      <div className="p-6 border-t border-surface-dim bg-background">
        <div className="relative group">
          <input
            className="w-full bg-white border border-surface-dim py-4 px-6 focus:outline-none focus:ring-1 focus:ring-ink transition-all font-bold text-sm placeholder:text-[#888] text-ink"
            placeholder="INPUT STRICTLY FORMATTED QUERIES..."
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
          />
          <button 
            onClick={handleSend}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-ink hover:text-white transition-colors p-2 bg-background border border-surface-dim hover:bg-ink cursor-pointer"
          >
            <ArrowRight className="w-5 h-5" strokeWidth={2} />
          </button>
        </div>
      </div>
    </section>
  );
}

import { ArrowLeft, Terminal as TerminalIcon } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAppStore } from "../store/appStore";
import { useEffect, useRef } from "react";

export default function Terminal() {
  const navigate = useNavigate();
  const { messages, wsConnected } = useAppStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  return (
    <div className="h-screen w-screen bg-[#F4F4F2] md:p-6 lg:p-10 box-border flex flex-col font-mono text-ink">
      <div className="flex-1 bg-black border-[3px] border-black shadow-[6px_6px_0_#000] flex flex-col p-6 sm:p-10 relative overflow-hidden text-[#14F195]">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#333] pb-6 mb-6">
          <button 
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-3 font-bold text-sm uppercase tracking-widest hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="hidden sm:inline">Terminate Session</span>
          </button>
          <div className="flex items-center gap-4">
            <span className="font-bold text-sm uppercase tracking-widest opacity-50">PORT: 8000</span>
            <div className={`px-3 py-1 font-bold text-[10px] uppercase tracking-widest ${wsConnected ? 'bg-[#14F195] text-black' : 'bg-yellow-500 text-black'}`}>
              {wsConnected ? 'V-SOCKET ALIVE' : 'DATALINK PENDING'}
            </div>
          </div>
        </div>

        {/* Console Log */}
        <div className="flex-1 overflow-y-auto space-y-2 pr-4 custom-scrollbar text-sm opacity-90">
          <div className="mb-6">
            <p>==================================================</p>
            <p>KINETIC_SYS // TELEMETRY TERMINAL V2.4</p>
            <p>INITIALIZING SECURE DATALINK ... [OK]</p>
            <p>ESTABLISHING WEBSOCKET TO 127.0.0.1:8000 ... [{wsConnected ? 'SUCCESS' : 'PENDING'}]</p>
            <p>==================================================</p>
          </div>

          {messages.map((msg, i) => (
            <div key={i} className="flex flex-col mb-4">
              <span className="opacity-50">[{new Date().toISOString()}] - MSG_{msg.id} ({msg.tokens})</span>
              <span className={`${msg.isUser ? 'text-white' : 'text-[#14F195]'}`}>{'> '} {msg.text}</span>
            </div>
          ))}
          
          <div ref={bottomRef} className="pt-4 flex items-center gap-2 animate-pulse">
            <TerminalIcon className="w-4 h-4" />
            <span>_</span>
          </div>
        </div>

      </div>
    </div>
  );
}

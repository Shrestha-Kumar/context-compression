import React, { useEffect, useState } from 'react';
import { ArrowLeft, Clock, MessageSquare, Trash2, Play } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface Session {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export default function Sessions() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/sessions')
      .then(res => res.json())
      .then(data => {
        setSessions(data.sessions || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch sessions:", err);
        setLoading(false);
      });
  }, []);

  const handleDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm("Delete this session?")) {
      fetch(`http://localhost:8000/sessions/${id}`, { method: 'DELETE' })
        .then(() => setSessions(prev => prev.filter(s => s.id !== id)));
    }
  };

  const handleResume = (id: string) => {
    navigate(`/compression?session_id=${id}`);
  };

  return (
    <div className="h-screen w-screen bg-[#F4F4F2] md:p-6 lg:p-10 box-border flex flex-col font-sans overflow-hidden text-ink">
      <div className="flex-1 bg-white border-[3px] border-black shadow-[6px_6px_0_#000] relative flex flex-col items-center py-12 px-10">
        
        {/* Header */}
        <div className="w-full max-w-5xl flex items-center justify-between border-b-[3px] border-black pb-8 mb-10">
          <button 
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-3 font-black text-2xl uppercase tracking-tighter hover:text-[#888] transition-colors"
          >
            <ArrowLeft className="w-8 h-8" strokeWidth={3} />
            Back to Hub
          </button>
          <span className="font-sans font-black text-black uppercase tracking-tighter text-3xl">
            Chat<span className="outline-text">_HISTORY</span>
          </span>
        </div>

        {/* Content */}
        <div className="w-full max-w-5xl flex-1 overflow-y-auto pr-4 custom-scrollbar">
          {loading ? (
            <div className="text-center py-20 font-black uppercase tracking-widest opacity-20 text-4xl mt-20">
              Initializing...
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-20 border-[3px] border-dashed border-black/10 rounded-xl">
              <MessageSquare className="w-16 h-16 mx-auto mb-6 opacity-10" />
              <h3 className="font-black text-2xl uppercase tracking-tighter text-black/20">No active sessions found</h3>
              <p className="text-black/20 text-sm mt-2">Start a new chat in the main dashboard to generate history.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6 pb-10">
              {sessions.map((session) => (
                <div 
                  key={session.id}
                  onClick={() => handleResume(session.id)}
                  className="border-[3px] border-black p-6 bg-surface shadow-[4px_4px_0_#000] hover:shadow-[8px_8px_0_#000] hover:-translate-x-1 hover:-translate-y-1 transition-all cursor-pointer group flex items-center justify-between"
                >
                  <div className="flex items-center gap-6">
                    <div className="w-12 h-12 bg-black text-white flex items-center justify-center font-black rounded-sm group-hover:bg-[#333]">
                      <Clock className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="font-black text-xl uppercase tracking-tighter mb-1">{session.name}</h3>
                      <div className="flex items-center gap-4 text-[10px] font-bold uppercase tracking-widest text-[#888]">
                        <span>ID: {session.id.slice(0, 8)}</span>
                        <span>•</span>
                        <span>Updated: {new Date(session.updated_at).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <button 
                      onClick={(e) => handleDelete(session.id, e)}
                      className="p-3 border-[2px] border-black hover:bg-red-500 hover:text-white transition-colors"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                    <div className="bg-black text-white p-3 border-[2px] border-black group-hover:bg-[#333]">
                      <Play className="w-5 h-5 fill-current" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

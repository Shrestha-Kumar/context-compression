import { ArrowLeft, Box } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function TemplatePage({ title, context }: { title: string, context: string }) {
  const navigate = useNavigate();

  return (
    <div className="h-screen w-screen bg-[#F4F4F2] md:p-6 lg:p-10 box-border flex flex-col font-sans overflow-hidden text-ink">
      <div className="flex-1 bg-white border-[3px] border-black shadow-[6px_6px_0_#000] relative flex flex-col items-center py-20 px-10">
        
        {/* Header */}
        <div className="w-full max-w-4xl flex items-center justify-between border-b-[3px] border-black pb-8 mb-10">
          <button 
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-3 font-black text-2xl uppercase tracking-tighter hover:text-[#888] transition-colors"
          >
            <ArrowLeft className="w-8 h-8" strokeWidth={3} />
            Back to Hub
          </button>
          <span className="font-sans font-black text-black uppercase tracking-tighter text-3xl">
            {title}<span className="outline-text">_SYS</span>
          </span>
        </div>

        {/* Content */}
        <div className="w-full max-w-4xl flex-1 flex flex-col items-center justify-center border-[2px] border-dashed border-[#ccc] bg-[#fcfcfc]">
          <Box className="w-12 h-12 text-[#ccc] mb-4" strokeWidth={1} />
            <h2 className="text-[10px] font-bold tracking-widest uppercase mb-2">
              MODULE UNDER CONSTRUCTION
            </h2>
            <p className="max-w-[300px] text-[8px] uppercase tracking-widest leading-relaxed">
              THIS IS A FRONTEND UI PLACEHOLDER. THE EXTENDED TELEMETRY DATALINK FOR {title.toUpperCase()} IS PENDING FUTURE INTEGRATION.
            </p>
        </div>

      </div>
    </div>
  );
}

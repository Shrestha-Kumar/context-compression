import { ArrowLeft, Settings2, Sliders, Upload, Play } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function Settings() {
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
            Global<span className="outline-text">_CFG</span>
          </span>
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-10 w-full max-w-4xl flex-1">
          {/* Card 1 */}
          <div className="border-[2px] border-black p-8 bg-surface shadow-[4px_4px_0_#000] flex flex-col group cursor-pointer hover:-translate-y-1 transition-transform">
            <Sliders className="w-10 h-10 mb-6 group-hover:scale-110 transition-transform" strokeWidth={2} />
            <h3 className="font-black text-2xl uppercase tracking-tighter mb-3">Model Parameters</h3>
            <p className="text-[#666] text-sm leading-relaxed mb-8 flex-1">
              Adjust sampling temperatures, configure Top-K restraints, and force exact penalty distributions on the INT4 local backbone.
            </p>
            <button className="bg-black text-white px-6 py-3 font-bold text-xs tracking-widest uppercase hover:bg-[#333] w-full mt-auto">Configure</button>
          </div>

          {/* Card 2 */}
          <div className="border-[2px] border-black p-8 bg-surface shadow-[4px_4px_0_#000] flex flex-col group cursor-pointer hover:-translate-y-1 transition-transform">
            <Settings2 className="w-10 h-10 mb-6 group-hover:scale-110 transition-transform" strokeWidth={2} />
            <h3 className="font-black text-2xl uppercase tracking-tighter mb-3">Compression Rules</h3>
            <p className="text-[#666] text-sm leading-relaxed mb-8 flex-1">
              Define target pruning ratios, set sliding window boundaries, and define strict non-pruning keywords for the LLM judge.
            </p>
            <button className="bg-white text-black border-[2px] border-black px-6 py-3 font-bold text-xs tracking-widest uppercase hover:bg-black hover:text-white transition-colors w-full mt-auto">System Constraints</button>
          </div>
        </div>

      </div>
    </div>
  );
}

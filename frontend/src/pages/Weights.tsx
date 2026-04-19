import { TopNav } from "../components/dashboard/TopNav";
import { SideNav } from "../components/dashboard/SideNav";
import { ArrowLeft, BrainCircuit } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function Weights() {
  const navigate = useNavigate();

  return (
    <div className="h-screen w-screen bg-[#F4F4F2] md:p-6 lg:p-10 box-border flex font-sans overflow-hidden relative text-ink">
      <div className="flex-1 w-full h-full bg-white grid grid-cols-[60px_1fr] md:grid-cols-[80px_1fr] grid-rows-[60px_1fr] md:grid-rows-[80px_1fr] overflow-hidden shadow-2xl">

        {/* Left Rail */}
        <div className="col-start-1 row-start-1 row-span-2 bg-black text-white flex flex-col relative z-20 overflow-hidden">
          <SideNav />
        </div>

        {/* Header */}
        <header className="col-start-2 row-start-1 flex items-center border-[2px] border-black bg-white relative z-10 w-full overflow-hidden mb-[-2px]">
          <TopNav />
        </header>

        {/* Main Content Area */}
        <main className="col-start-2 row-start-2 flex overflow-hidden border-[3px] border-black border-t-0 p-8 lg:p-12 relative flex-col gap-8 font-mono text-ink bg-[#fcfcfc]">
          <div className="flex items-center justify-between border-b-[3px] border-black pb-4 pt-4">
            <button 
              onClick={() => navigate('/dashboard')}
              className="group flex items-center gap-3 font-black text-xl lg:text-2xl uppercase tracking-tighter hover:text-[#888] transition-colors"
            >
              <ArrowLeft className="w-8 h-8 group-hover:-translate-x-1 transition-transform" strokeWidth={4} />
              Weights <span className="outline-text">_CFG</span>
            </button>
            <BrainCircuit className="w-10 h-10 text-black animate-pulse" strokeWidth={2.5} />
          </div>

          <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-8 overflow-y-auto no-scrollbar pb-6">
            
            {/* Base Model Specs */}
            <div className="border-[3px] border-black p-8 bg-white shadow-[6px_6px_0_#000] flex flex-col h-fit">
              <h2 className="font-black text-xl uppercase tracking-[0.2em] mb-8 border-b-[3px] border-black pb-3">Base Backbone</h2>
              <div className="flex flex-col gap-6 flex-1">
                <div className="flex justify-between items-end border-b-2 border-surface-dim pb-3">
                  <span className="text-[10px] text-[#888] uppercase tracking-[0.15em] font-black">Model_ID</span>
                  <span className="text-lg font-black uppercase">QWEN2.5-1.5B</span>
                </div>
                <div className="flex justify-between items-end border-b-2 border-surface-dim pb-3">
                  <span className="text-[10px] text-[#888] uppercase tracking-[0.15em] font-black">Quantization</span>
                  <span className="text-lg font-black uppercase text-[#222]">4-BIT (BNB)</span>
                </div>
                <div className="flex justify-between items-end border-b-2 border-surface-dim pb-3">
                  <span className="text-[10px] text-[#888] uppercase tracking-[0.15em] font-black">Max_Ctx_Len</span>
                  <span className="text-lg font-black uppercase">32,768 TOK</span>
                </div>
                <div className="flex justify-between items-end border-b-2 border-surface-dim pb-3">
                  <span className="text-[10px] text-[#888] uppercase tracking-[0.15em] font-black">Attention</span>
                  <span className="text-lg font-black uppercase">SINKING_KV</span>
                </div>
              </div>
            </div>

            {/* LoRA Adapters Specs */}
            <div className="border-[3px] border-black p-8 bg-black text-white shadow-[6px_6px_0_#14F195] flex flex-col h-fit">
              <h2 className="font-black text-xl uppercase tracking-[0.2em] mb-8 border-b-[3px] border-[#14F195]/30 pb-3 text-[#14F195]">LoRA Params</h2>
              <div className="flex flex-col gap-6 flex-1">
                <div className="flex justify-between items-end border-b border-[#333] pb-3">
                  <span className="text-[10px] text-[#888] uppercase tracking-[0.15em] font-black">Rank (R)</span>
                  <span className="text-xl font-black uppercase text-[#14F195]">16</span>
                </div>
                <div className="flex justify-between items-end border-b border-[#333] pb-3">
                  <span className="text-[10px] text-[#888] uppercase tracking-[0.15em] font-black">Alpha</span>
                  <span className="text-xl font-black uppercase text-[#14F195]">32</span>
                </div>
                <div className="flex flex-col gap-2 border-b border-[#333] pb-3">
                  <span className="text-[10px] text-[#888] uppercase tracking-[0.15em] font-black">Target Modules</span>
                  <span className="text-[12px] font-black text-[#14F195] leading-relaxed">
                    [ q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj ]
                  </span>
                </div>
                <div className="flex justify-between items-center bg-[#111] p-4 mt-4 border-l-[4px] border-[#14F195]">
                  <span className="text-[10px] text-[#888] uppercase tracking-[0.2em] font-black">Adapter_HASH</span>
                  <span className="text-[12px] font-black uppercase text-yellow-500">CKPT_63_STABLE</span>
                </div>
              </div>
            </div>

          </div>
        </main>
      </div>
    </div>
  );
}

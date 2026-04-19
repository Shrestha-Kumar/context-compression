import { TopNav } from "../components/dashboard/TopNav";
import { SideNav } from "../components/dashboard/SideNav";
import { Activity, ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAppStore } from "../store/appStore";

export default function Latency() {
  const navigate = useNavigate();
  const { metrics, kvCacheMetrics } = useAppStore();

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

        {/* Main Content */}
        <main className="col-start-2 row-start-2 flex overflow-hidden border-[3px] border-black border-t-0 p-8 lg:p-12 relative flex-col gap-8 font-mono text-ink bg-white">
          <div className="flex items-center justify-between border-b-[3px] border-black pb-4 pt-4">
            <button 
              onClick={() => navigate('/dashboard')}
              className="group flex items-center gap-3 font-black text-xl lg:text-2xl uppercase tracking-tighter hover:text-[#888] transition-colors"
            >
              <ArrowLeft className="w-8 h-8 group-hover:-translate-x-1 transition-transform" strokeWidth={4} />
              Performance <span className="outline-text">_LOG</span>
            </button>
            <Activity className="w-10 h-10 text-black animate-pulse" strokeWidth={2.5} />
          </div>

          <div className="flex flex-col md:flex-row gap-6 mb-2">
            <div className="flex-1 bg-white border-[3px] border-black p-6 shadow-[6px_6px_0_#000]">
              <span className="font-black text-[10px] text-[#888] uppercase tracking-[0.2em] mb-2 block">System Compression Ratio</span>
              <div className="text-3xl font-black tracking-tighter">{metrics.compRatio ? `${(metrics.compRatio * 100).toFixed(1)}%` : '0%'}</div>
            </div>
            
            <div className="flex-1 bg-black text-white border-[3px] border-black p-6 shadow-[6px_6px_0_#14F195]">
              <span className="font-black text-[10px] text-[#888] uppercase tracking-[0.2em] mb-2 block">KV Buffer Evictions</span>
              <div className="text-3xl font-black tracking-tighter text-[#14F195]">{(kvCacheMetrics?.evicted_count || 0).toLocaleString()}</div>
              <div className="text-[10px] text-[#888] mt-2 font-black tracking-[0.2em]">/ {(kvCacheMetrics?.window_size || 0).toLocaleString()} TOK</div>
            </div>
          </div>

          <div className="flex-1 border-[3px] border-black relative overflow-hidden bg-background flex flex-col shadow-[10px_10px_0_#000]">
            <div className="h-10 bg-black text-white flex items-center px-6 font-black text-[10px] uppercase tracking-[0.3em] justify-between shrink-0">
              <span>LATENCY_TRACES</span>
              <span>HISTORICAL</span>
            </div>
            <div className="flex flex-col p-6 overflow-y-auto no-scrollbar bg-white">
              <div className="grid grid-cols-5 px-6 py-3 font-black text-[10px] tracking-[0.2em] border-b-[3px] border-black text-ink uppercase mb-4 bg-[#F8F8F8]">
                <span>TIMESTAMP</span>
                <span>OP_TYPE</span>
                <span>LAYER</span>
                <span>TIME_DELTA</span>
                <span>STATE</span>
              </div>
              
              {/* Static demo traces, to represent architectural breakdown */}
              {[
                { time: "05.102ms", op: "KV_PACK", layer: "L_0-24", ms: "12.44ms", state: "OK" },
                { time: "18.341ms", op: "ATTN_FWD", layer: "L_12", ms: "45.21ms", state: "OK" },
                { time: "63.003ms", op: "MLP_FWD", layer: "L_12", ms: "32.10ms", state: "OK" },
                { time: "95.104ms", op: "ATTN_FWD", layer: "L_24", ms: "40.92ms", state: "OK" },
                { time: "135.02ms", op: "TOKENIZE", layer: "IN/OUT", ms: "1.40ms", state: "PASS" },
                { time: "140.23ms", op: "KV_PRUNE", layer: "HEADS", ms: "0.85ms", state: "EVICT" },
              ].map((row, i) => (
                <div key={i} className="grid grid-cols-5 px-6 py-3 font-black text-[12px] border-b border-surface-dim hover:bg-[#F8F8F8] transition-colors cursor-default text-ink group">
                  <span className="text-[#888] group-hover:text-black">{row.time}</span>
                  <span className="uppercase tracking-widest">{row.op}</span>
                  <span className="opacity-60">{row.layer}</span>
                  <span className="font-black text-[14px] tracking-tighter">{row.ms}</span>
                  <span className={`font-black uppercase px-2 py-0.5 w-max text-[9px] tracking-widest ${row.state === 'EVICT' ? 'bg-red-500 text-white' : 'bg-black text-[#14F195]'}`}>{row.state}</span>
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

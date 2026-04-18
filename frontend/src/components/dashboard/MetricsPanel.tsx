import { useState } from 'react';
import { useAppStore } from "../../store/appStore";

export function MetricsPanel() {
  const { metrics, tokenHeatmap, kvCacheMetrics } = useAppStore();
  const [activeTab, setActiveTab] = useState<'METRICS' | 'HEATMAP' | 'KV-CACHE'>('METRICS');

  return (
    <div className="flex-1 flex flex-col bg-white min-w-[360px] h-full z-10 border-r border-surface-dim cursor-grab active:cursor-grabbing">
      <div className="h-16 flex items-center border-b border-surface-dim px-8 gap-8 bg-background">
        <button className="font-bold text-[10px] uppercase tracking-[0.2em] text-black border-b-[4px] border-black h-full px-2 pt-2">
          METRICS
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-8 flex flex-col gap-8 no-scrollbar bg-white">
        
        {/* Tab Header */}
        <div className="flex items-center gap-8 border-b border-[#000] pb-2 select-none">
          {['METRICS', 'HEATMAP', 'KV-CACHE'].map((tab) => (
            <span 
              key={tab}
              onClick={() => setActiveTab(tab as typeof activeTab)}
              className={`font-bold text-[10px] uppercase tracking-[0.2em] cursor-pointer transition-colors relative ${activeTab === tab ? 'text-ink' : 'text-[#888] hover:text-[#555]'}`}
            >
              {tab}
              {activeTab === tab && <div className="absolute -bottom-[9px] left-0 right-0 h-[2px] bg-ink"></div>}
            </span>
          ))}
        </div>

        {/* Global KPI Summary */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-surface p-5 border border-surface-dim shadow-sm">
            <span className="font-bold text-[9px] text-[#888] uppercase tracking-[0.2em]">Comp. Ratio</span>
            <div className="text-3xl font-black text-ink mt-2 tracking-tighter">{metrics.compRatio}%</div>
          </div>
          <div className="bg-surface p-5 border border-surface-dim shadow-sm">
            <span className="font-bold text-[9px] text-[#888] uppercase tracking-[0.2em]">Tokens</span>
            <div className="text-3xl font-black text-ink mt-2 tracking-tighter">{metrics.tokens}</div>
          </div>
          <div className="bg-surface p-5 border border-surface-dim shadow-sm">
            <span className="font-bold text-[9px] text-[#888] uppercase tracking-[0.2em]">VRAM</span>
            <div className="text-3xl font-black text-ink mt-2 tracking-tighter">1.2/6.0</div>
          </div>
          <div className="bg-surface p-5 border border-surface-dim shadow-sm">
            <span className="font-bold text-[9px] text-[#888] uppercase tracking-[0.2em]">Turn</span>
            <div className="text-3xl font-black text-ink mt-2 tracking-tighter">{metrics.turn}</div>
          </div>
        </div>

        {/* Dynamic Tab Content */}
        <div className="flex-1 min-h-[300px] flex flex-col">
          {activeTab === 'METRICS' && (
            <div className="flex-1 w-full border-[2px] border-[#000] p-6 relative flex flex-col">
              <div className="flex items-center justify-between font-bold text-[10px] text-[#888] uppercase tracking-[0.2em] mb-4">
                <span className="flex items-center gap-2"><div className="w-2 h-[2px] bg-[#E0E0E0]"></div> Raw_Signal</span>
                <span className="flex items-center gap-2"><div className="w-2 h-[2px] bg-[#000]"></div> Compressed_Data</span>
              </div>
              
              <div className="flex-1 relative mt-10">
                <div className="absolute inset-0 flex flex-col justify-between z-0 pointer-events-none opacity-20">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="w-full border-b border-dashed border-[#000]"></div>
                  ))}
                </div>
                <svg className="w-full h-full absolute inset-0 z-10" viewBox="0 0 100 100" preserveAspectRatio="none">
                  <path d="M0,80 L10,60 L20,90 L30,40 L40,70 L50,50 L60,80 L70,60 L80,90 L90,30 L100,50" fill="none" stroke="#E0E0E0" strokeWidth="1" vectorEffect="non-scaling-stroke" />
                  <path d="M0,70 L10,75 L20,72 L30,73 L40,68 L50,75 L60,72 L70,70 L80,74 L90,68 L100,70" fill="none" stroke="#000" strokeWidth="2" vectorEffect="non-scaling-stroke" />
                </svg>
              </div>
    
              <div className="flex justify-between mt-4 font-bold text-[8px] text-[#888] uppercase tracking-[0.2em]">
                <span>0ms</span>
                <span>250ms</span>
                <span>500ms</span>
                <span>750ms</span>
                <span>1000</span>
              </div>
            </div>
          )}

          {activeTab === 'HEATMAP' && (
            <div className="flex-1 w-full border-[2px] border-black p-4 overflow-y-auto no-scrollbar relative min-h-[250px]">
              <span className="absolute top-2 right-4 text-[8px] text-[#888] uppercase font-bold tracking-[0.2em]">
                Target: ~{metrics.compRatio}% Retention
              </span>
              {tokenHeatmap.length === 0 ? (
                <div className="absolute inset-0 flex items-center justify-center text-[10px] text-[#888] font-mono p-4 uppercase tracking-[0.2em]">
                  [AWAITING COMPRESSION GRAPH]
                </div>
              ) : (
                <div className="flex flex-wrap gap-[2px] text-xs font-mono leading-relaxed mt-6">
                  {tokenHeatmap.map((t, i) => (
                    <span key={i} className={`px-[3px] py-[2px] ${t.preserved ? "bg-[#14F195] text-black font-bold" : "bg-transparent text-[#888] opacity-[0.35]"} ${t.is_entity ? 'border-b border-black' : ''}`}>
                      {t.text}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'KV-CACHE' && (
            <div className="flex-1 w-full border-[2px] border-black p-6 relative flex flex-col font-mono min-h-[250px]">
              {!kvCacheMetrics ? (
                <div className="absolute inset-0 flex items-center justify-center text-[10px] text-[#888] uppercase tracking-[0.2em] text-center p-4">
                  [AWAITING INFERENCE ENGINE]
                </div>
              ) : (
                <div className="flex flex-col h-full justify-between">
                  <div>
                    <p className="text-[10px] text-[#888] uppercase tracking-widest mb-1">Sliding Window Allocated</p>
                    <p className="text-4xl font-black text-ink">{kvCacheMetrics.window_size.toLocaleString()} TOK</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-[#888] uppercase tracking-widest mb-1">Evicted Tokens (Previous Turn)</p>
                    <p className="text-3xl font-black text-red-500">{kvCacheMetrics.evicted_count.toLocaleString()}</p>
                  </div>
                  <div className="mt-6">
                    <div className="h-5 bg-[#E0E0E0] w-full border-[2px] border-black relative overflow-hidden">
                      <div className="absolute inset-y-0 left-0 bg-[#14F195] transition-all duration-500" style={{ width: `${Math.min(100, Math.max(0, 100 - (kvCacheMetrics.evicted_count/Math.max(1, kvCacheMetrics.window_size))*100))}%` }} />
                    </div>
                    <div className="flex justify-between items-center mt-2">
                      <p className="text-[9px] text-[#888] uppercase tracking-widest font-bold">Base VRAM Retention Rate</p>
                      <p className="text-[9px] text-black font-bold uppercase tracking-widest">
                        {Math.max(0, 100 - (kvCacheMetrics.evicted_count/Math.max(1, kvCacheMetrics.window_size))*100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Static Latency Log at bottom */}
        {activeTab === 'METRICS' && (
          <div className="flex flex-col gap-4 mt-8">
            <span className="font-bold text-[10px] text-ink uppercase tracking-[0.2em]">
              Latency Log
            </span>
            <div className="border border-surface-dim bg-white">
              <div className="grid grid-cols-4 px-5 py-3 font-bold text-[10px] tracking-widest bg-ink text-surface uppercase">
                <span>OP_TYPE</span>
                <span>LAYER</span>
                <span>MS_DELTA</span>
                <span>STATUS</span>
              </div>
              {[
                { op: "KV_PACK", layer: "L_24", ms: "12.4", status: "SUCCESS" },
                { op: "HEAD_MERGE", layer: "L_24", ms: "8.1", status: "SUCCESS" },
                { op: "SPARSE_ATTN", layer: "L_25", ms: "45.2", status: "SUCCESS" },
                { op: "TENSOR_ROT", layer: "L_25", ms: "0.4", status: "SUCCESS" }
              ].map((row, i) => (
                <div key={i} className="grid grid-cols-4 px-5 py-3 font-bold text-[10px] text-ink border-t border-surface-dim hover:bg-background transition-colors">
                  <span className="uppercase">{row.op}</span>
                  <span>{row.layer}</span>
                  <span>{row.ms}</span>
                  <span className="font-black">{row.status}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

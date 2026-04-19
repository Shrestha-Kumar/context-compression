import React, { useState, useCallback, useRef, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useAppStore } from "../../store/appStore";

interface MetricsPanelProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  width: number;
  onResizeStart: (e: React.MouseEvent) => void;
}

export function MetricsPanel({ collapsed, onToggleCollapse, width, onResizeStart }: MetricsPanelProps) {
  const { metrics, kvCacheMetrics } = useAppStore();
  const [activeTab, setActiveTab] = useState<'METRICS' | 'KV-CACHE'>('METRICS');
  const [history, setHistory] = useState<{raw: number, comp: number}[]>(Array(10).fill({raw: 0, comp: 0}));

  useEffect(() => {
    if (metrics.tokens > 0) {
      setHistory(prev => {
        const estRaw = Math.floor(metrics.tokens / Math.max(0.01, (1 - metrics.compRatio)));
        const next = [...prev, { raw: estRaw, comp: metrics.tokens }];
        return next.slice(-20);
      });
    }
  }, [metrics]);

  const maxRaw = Math.max(...history.map(d => d.raw), 100);
  const getPoints = (key: 'raw'|'comp') => history.map((d, i) => {
    const x = (i / Math.max(1, history.length - 1)) * 100;
    const y = 90 - ((d[key] / maxRaw) * 60);
    return `${x},${y}`;
  }).join(' L');

  if (collapsed) {
    return (
      <div className="h-full flex flex-col items-center bg-background border-r border-surface-dim z-10 w-[40px] shrink-0">
        <button
          onClick={onToggleCollapse}
          className="mt-4 text-ink hover:bg-surface-dim transition-colors p-2 w-full flex justify-center"
          title="Expand Metrics"
        >
          <ChevronRight className="w-4 h-4" strokeWidth={2.5} />
        </button>
        <div className="flex-1 flex items-center justify-center">
          <span className="[writing-mode:vertical-rl] rotate-180 uppercase tracking-[0.3em] text-[9px] font-bold text-[#888] whitespace-nowrap">
            METRICS
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex" style={{ width }}>
      {/* Panel body */}
      <div className="flex-1 flex flex-col bg-white border-r border-surface-dim z-10 overflow-hidden">
        {/* Panel header */}
        <div className="h-16 flex items-center border-b border-surface-dim px-6 gap-6 bg-background shrink-0 justify-between">
          <div className="flex items-center gap-6">
            {(['METRICS', 'KV-CACHE'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`font-bold text-[10px] uppercase tracking-[0.2em] h-full px-1 pt-1 transition-colors border-b-[4px] ${
                  activeTab === tab
                    ? 'text-ink border-black'
                    : 'text-[#888] hover:text-ink border-transparent'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
          <button
            onClick={onToggleCollapse}
            className="text-[#888] hover:text-ink transition-colors p-1"
            title="Collapse Metrics"
          >
            <ChevronLeft className="w-4 h-4" strokeWidth={2.5} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6 no-scrollbar bg-white">

          {/* KPI Cards — always visible */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-surface p-4 border border-surface-dim shadow-sm">
              <span className="font-bold text-[9px] text-[#888] uppercase tracking-[0.2em]">Comp. Ratio</span>
              <div className="text-2xl font-black text-ink mt-1 tracking-tighter">
                {metrics.compRatio ? `${(metrics.compRatio * 100).toFixed(1)}%` : '%'}
              </div>
            </div>
            <div className="bg-surface p-4 border border-surface-dim shadow-sm">
              <span className="font-bold text-[9px] text-[#888] uppercase tracking-[0.2em]">Tokens</span>
              <div className="text-2xl font-black text-ink mt-1 tracking-tighter">{metrics.tokens || '—'}</div>
            </div>
            <div className="bg-surface p-4 border border-surface-dim shadow-sm">
              <span className="font-bold text-[9px] text-[#888] uppercase tracking-[0.2em]">VRAM</span>
              <div className="text-2xl font-black text-ink mt-1 tracking-tighter">1.2/6.0</div>
            </div>
            <div className="bg-surface p-4 border border-surface-dim shadow-sm">
              <span className="font-bold text-[9px] text-[#888] uppercase tracking-[0.2em]">Turn</span>
              <div className="text-2xl font-black text-ink mt-1 tracking-tighter">{metrics.turn}</div>
            </div>
          </div>

          {/* Tab content */}
          <div className="flex-1 flex flex-col min-h-[200px]">
            {activeTab === 'METRICS' && (
              <div className="flex-1 w-full border-[2px] border-[#000] p-4 relative flex flex-col">
                <div className="flex items-center justify-between font-bold text-[10px] text-[#888] uppercase tracking-[0.2em] mb-3">
                  <span className="flex items-center gap-2">
                    <div className="w-3 h-[2px] bg-[#E0E0E0]" />
                    Raw_Signal
                  </span>
                  <span className="flex items-center gap-2">
                    <div className="w-3 h-[2px] bg-[#000]" />
                    Compressed_Data
                  </span>
                </div>
                <div className="flex-1 relative min-h-[120px]">
                  <div className="absolute inset-0 flex flex-col justify-between z-0 pointer-events-none opacity-20">
                    {[...Array(4)].map((_, i) => (
                      <div key={i} className="w-full border-b border-dashed border-[#000]" />
                    ))}
                  </div>
                  <svg className="w-full h-full absolute inset-0 z-10" viewBox="0 0 100 100" preserveAspectRatio="none">
                    <path d={`M0,90 L${getPoints('raw')}`} fill="none" stroke="#E0E0E0" strokeWidth="1" vectorEffect="non-scaling-stroke" />
                    <path d={`M0,90 L${getPoints('comp')}`} fill="none" stroke="#000" strokeWidth="2" vectorEffect="non-scaling-stroke" />
                  </svg>
                </div>
                <div className="flex justify-between mt-2 font-bold text-[8px] text-[#888] uppercase tracking-[0.2em]">
                  <span>0ms</span><span>250ms</span><span>500ms</span><span>750ms</span><span>1000</span>
                </div>
              </div>
            )}

            {activeTab === 'KV-CACHE' && (
              <div className="flex-1 w-full border-[2px] border-black p-5 relative flex flex-col font-mono min-h-[200px]">
                {!kvCacheMetrics ? (
                  <div className="absolute inset-0 flex items-center justify-center text-[10px] text-[#888] uppercase tracking-[0.2em] text-center p-4">
                    [AWAITING INFERENCE ENGINE]
                  </div>
                ) : (
                  <div className="flex flex-col h-full justify-between gap-4">
                    <div>
                      <p className="text-[10px] text-[#888] uppercase tracking-widest mb-1">Sliding Window Allocated</p>
                      <p className="text-3xl font-black text-ink">{kvCacheMetrics.window_size.toLocaleString()} TOK</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-[#888] uppercase tracking-widest mb-1">Evicted Tokens (Prev Turn)</p>
                      <p className="text-2xl font-black text-red-500">{kvCacheMetrics.evicted_count.toLocaleString()}</p>
                    </div>
                    <div>
                      <div className="h-4 bg-[#E0E0E0] w-full border-[2px] border-black relative overflow-hidden">
                        <div
                          className="absolute inset-y-0 left-0 bg-black transition-all duration-500"
                          style={{ width: `${Math.min(100, Math.max(0, 100 - (kvCacheMetrics.evicted_count / Math.max(1, kvCacheMetrics.window_size)) * 100))}%` }}
                        />
                      </div>
                      <div className="flex justify-between items-center mt-1">
                        <p className="text-[9px] text-[#888] uppercase tracking-widest font-bold">Base VRAM Retention</p>
                        <p className="text-[9px] text-black font-bold uppercase tracking-widest">
                          {Math.max(0, 100 - (kvCacheMetrics.evicted_count / Math.max(1, kvCacheMetrics.window_size)) * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Latency Log — only on METRICS tab */}
          {activeTab === 'METRICS' && (
            <div className="flex flex-col gap-3">
              <span className="font-bold text-[10px] text-ink uppercase tracking-[0.2em]">Latency Log</span>
              <div className="border border-surface-dim bg-white">
                <div className="grid grid-cols-4 px-4 py-2 font-bold text-[9px] tracking-widest bg-ink text-surface uppercase">
                  <span>OP_TYPE</span><span>LAYER</span><span>MS_Δ</span><span>STATUS</span>
                </div>
                {[
                  { op: "KV_PACK", layer: "L_24", ms: "12.4", status: "OK" },
                  { op: "HEAD_MERGE", layer: "L_24", ms: "8.1", status: "OK" },
                  { op: "SPARSE_ATTN", layer: "L_25", ms: "45.2", status: "OK" },
                  { op: "TENSOR_ROT", layer: "L_25", ms: "0.4", status: "OK" },
                ].map((row, i) => (
                  <div key={i} className="grid grid-cols-4 px-4 py-2 font-bold text-[9px] text-ink border-t border-surface-dim hover:bg-background transition-colors">
                    <span className="uppercase">{row.op}</span>
                    <span>{row.layer}</span>
                    <span>{row.ms}</span>
                    <span className="font-black text-[#14F195] bg-black px-1">{row.status}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Drag handle */}
      <div
        onMouseDown={onResizeStart}
        className="w-[5px] bg-surface-dim hover:bg-ink cursor-col-resize transition-colors shrink-0 z-20 flex items-center justify-center group"
        title="Drag to resize"
      >
        <div className="w-[1px] h-8 bg-[#ccc] group-hover:bg-white transition-colors" />
      </div>
    </div>
  );
}

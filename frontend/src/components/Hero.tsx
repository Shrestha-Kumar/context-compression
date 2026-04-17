import React from 'react';

export function Hero() {
  return (
    <section className="relative min-h-[calc(100vh-80px)] px-[60px] py-[40px] flex flex-col justify-center overflow-hidden">
      <div className="relative z-10 max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-2 gap-[40px] items-center">
        <div className="flex flex-col justify-center pr-[20px]">
          <div className="text-[12px] uppercase tracking-[4px] mb-[24px] text-ink-lighter font-sans">
            Version 4.0 // Stable Release
          </div>
          <h1 className="text-[72px] leading-[0.95] font-light mb-[32px] tracking-[-2px] text-ink">
            Infinite Context.<br/>
            Zero Latency.
          </h1>
          <p className="text-[16px] leading-[1.6] text-ink-light mb-[48px] max-w-[400px]">
            A brutalist approach to LLM memory. Compress terabytes of unstructured context into surgical tokens without losing the signal in the noise.
          </p>
          <div className="flex flex-wrap gap-4 relative z-40">
            <button className="w-fit bg-ink text-surface px-[48px] py-[20px] font-semibold text-[13px] uppercase tracking-[2px] hover:opacity-80 transition-opacity cursor-pointer">
              Deploy Pipeline
            </button>
            <button className="w-fit bg-transparent border border-surface-dim text-ink px-[48px] py-[20px] font-semibold text-[13px] uppercase tracking-[2px] hover:bg-surface-dim transition-colors cursor-pointer">
              Read Whitepaper
            </button>
          </div>
        </div>
        
        <div className="grid grid-cols-2 grid-rows-2 gap-[20px]">
          <div className="bg-surface border border-surface-dim p-[30px] flex flex-col justify-end min-h-[240px] relative overflow-hidden">
            <div className="absolute top-[20px] right-[20px] w-[40px] h-[40px] border border-ink"></div>
            <span className="text-[10px] uppercase tracking-[2px] opacity-60 mb-[8px] text-ink font-sans">SYSTEM_LOAD</span>
            <div className="text-[24px] font-light text-ink">1.04ms</div>
            <span className="text-[10px] uppercase tracking-[2px] opacity-60 mt-[8px] text-ink">PER TOKEN INFERENCE</span>
          </div>
          <div className="bg-ink text-surface p-[30px] flex flex-col justify-end min-h-[240px] relative overflow-hidden">
            <div className="absolute top-[20px] right-[20px] w-[40px] h-[40px] border border-surface rounded-full"></div>
            <span className="text-[10px] uppercase tracking-[2px] opacity-60 mb-[8px] text-surface font-sans">REDUCTION</span>
            <div className="text-[24px] font-light text-surface">94%</div>
            <span className="text-[10px] uppercase tracking-[2px] opacity-60 mt-[8px] text-surface">VRAM SAVINGS</span>
          </div>
        </div>
      </div>
    </section>
  );
}

import React from 'react';

export function EvalHarness() {
  return (
    <section id="eval_harness" className="py-[80px] px-[60px] relative">
      <div className="max-w-7xl mx-auto relative z-10">
        <div className="bg-surface border border-surface-dim relative overflow-hidden flex flex-col lg:flex-row">
          <div className="lg:w-3/5 p-[40px] lg:p-[60px] flex flex-col justify-center">
            <span className="text-[12px] uppercase tracking-[4px] text-ink-lighter mb-[16px]">// EVAL_HARNESS</span>
            <h2 className="text-[48px] leading-[0.95] font-light tracking-[-1px] mb-[24px] text-ink">See the numbers.</h2>
            <p className="text-[16px] leading-[1.6] text-ink-light mb-[48px] max-w-[400px]">
              Benchmark your context reduction in seconds. Run our harness against the Needle-in-a-Haystack test and see zero performance loss at 10x compression.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-[40px] mb-[48px]">
              <div>
                <div className="text-[32px] font-light text-ink mb-[8px]">88.4%</div>
                <div className="text-[10px] uppercase tracking-[2px] text-ink-lighter font-medium">Token reduction</div>
              </div>
              <div>
                <div className="text-[32px] font-light text-ink mb-[8px]">99.8%</div>
                <div className="text-[10px] uppercase tracking-[2px] text-ink-lighter font-medium">Needle test</div>
              </div>
              <div>
                <div className="text-[32px] font-light text-ink mb-[8px]">2.1GB</div>
                <div className="text-[10px] uppercase tracking-[2px] text-ink-lighter font-medium">VRAM footprint</div>
              </div>
            </div>
            
            <button className="w-fit bg-ink text-surface px-[48px] py-[20px] font-semibold text-[13px] uppercase tracking-[2px] hover:opacity-80 transition-opacity">
              RUN EVAL_HARNESS.PY
            </button>
          </div>
          
          <div className="lg:w-2/5 min-h-[400px] border-l border-surface-dim relative">
            <img alt="Terminal interface showing performance data" className="absolute inset-0 w-full h-full object-cover grayscale opacity-90 mix-blend-multiply" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCAWjANVepfEjTGGEISS2OZ4r7KG1YkNKbHJxPUr4ztOQ9TTNiRu7LTNGJMts2cCODmk4B91KypUZiaOMvzut4_lId0JUpzB0VXFEiAmdYaNcWN5AZqqrhpQRRfLrY3ARltf7Q7sMyHa5m_0ImPVGIunezvqqxoZd2COzKfLlDSAT7JtcqnY-Scx7JWarWxyAd5uORD7F1zGTkJ4nOfTvFS9pJfFnT--vlnYNuqd2SSzYfWsfzVSwRyOGWvu15B8hcfVu8nG8j_goc"/>
          </div>
        </div>
      </div>
    </section>
  );
}

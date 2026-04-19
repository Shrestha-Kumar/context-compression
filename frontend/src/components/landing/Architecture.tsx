import React from 'react';

export function Architecture() {
  return (
    <section id="architecture" className="py-[80px] px-[60px] relative overflow-hidden">
      <div className="max-w-7xl mx-auto relative z-10">
        <div className="flex flex-col md:flex-row justify-between items-end mb-[40px] gap-8">
          <div>
            <span className="text-[12px] uppercase tracking-[4px] text-ink-lighter">// ARCHITECTURE</span>
            <h2 className="text-[48px] leading-[0.95] font-light mt-[16px] tracking-[-1px] text-ink">How compression happens.</h2>
          </div>
          <div className="border border-surface-dim px-[20px] py-[10px] bg-surface">
            <span className="text-[10px] text-ink uppercase tracking-[2px] font-bold">Pipeline V2 Engine Active</span>
          </div>
        </div>
        
        <div className="relative grid grid-cols-1 lg:grid-cols-4 gap-[20px]">
          {/* <!-- Step 01 --> */}
          <div className="bg-surface border border-surface-dim p-[30px] h-[240px] flex flex-col justify-end relative">
            <div className="absolute top-[20px] right-[20px] w-[40px] h-[40px] border border-ink opacity-20"></div>
            <div className="text-[24px] font-light text-ink mb-[16px]">01 // LoRA CoT Extraction</div>
            <p className="text-ink-light text-[14px] leading-[1.6]">Identifying non-negotiables through fine-tuned chain-of-thought logic.</p>
          </div>
          
          {/* <!-- Step 02 --> */}
          <div className="bg-ink text-surface p-[30px] h-[240px] flex flex-col justify-end relative">
            <div className="absolute top-[20px] right-[20px] w-[40px] h-[40px] border border-surface rounded-full opacity-20"></div>
            <div className="text-[24px] font-light text-surface mb-[16px]">02 // Memory State Mapping</div>
            <p className="text-surface opacity-70 text-[14px] leading-[1.6]">Synchronizing extracted constraints with real-time low-rank memory tensors.</p>
          </div>
          
          {/* <!-- Step 03 --> */}
          <div className="bg-surface border border-surface-dim p-[30px] h-[240px] flex flex-col justify-end relative">
            <div className="absolute top-[20px] right-[20px] w-[40px] h-[40px] border border-ink opacity-20"></div>
            <div className="text-[24px] font-light text-ink mb-[16px]">03 // Dynamic Token Pruning</div>
            <p className="text-ink-light text-[14px] leading-[1.6]">Aggressive context truncation based on pressure-aware validation gates.</p>
          </div>
          
          {/* <!-- Step 04 --> */}
          <div className="bg-ink text-surface p-[30px] h-[240px] flex flex-col justify-end relative">
            <div className="absolute top-[20px] right-[20px] w-[40px] h-[40px] border border-surface rounded-full opacity-20"></div>
            <div className="text-[24px] font-light text-surface mb-[16px]">04 // Attention Sink Inference</div>
            <p className="text-surface opacity-70 text-[14px] leading-[1.6]">Maintaining infinite-horizon KV cache stability with rolling-buffer logic.</p>
          </div>
        </div>
        
        <div className="mt-[40px] w-full aspect-[21/9] bg-black overflow-hidden relative border border-surface-dim">
          <img alt="Neural network architecture visualization" className="w-full h-full object-contain" src="/architecture.png"/>
          <div className="absolute bottom-[20px] left-[20px] bg-surface/90 px-[16px] py-[8px] border border-surface-dim">
            <p className="text-[10px] text-ink uppercase tracking-[2px] font-medium">System Schematic Visualization Rev 4.1</p>
          </div>
        </div>
      </div>
    </section>
  );
}

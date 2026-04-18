import React from 'react';
import { Cpu, Database, Terminal, Shield, Waypoints, BarChart } from 'lucide-react';

export function Capabilities() {
  return (
    <section className="py-[80px] px-[60px] relative">
      <div className="max-w-7xl mx-auto">
        <div className="mb-[40px] relative z-10">
          <span className="text-[12px] uppercase tracking-[4px] text-ink-lighter">// CAPABILITIES</span>
          <h2 className="text-[48px] leading-[0.95] font-light mt-[16px] mb-[32px] tracking-[-1px] text-ink">What the module does.</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-[20px] relative z-10">
          {/* Card 1 */}
          <div className="bg-surface border border-surface-dim p-[30px] flex flex-col justify-end min-h-[300px] relative overflow-hidden group hover:bg-ink hover:text-surface transition-colors duration-300">
            <Cpu className="absolute top-[30px] right-[30px] w-[32px] h-[32px] opacity-40 group-hover:opacity-100" strokeWidth={1} />
            <div>
              <span className="text-[10px] uppercase tracking-[2px] opacity-60 mb-[8px] block">01</span>
              <h3 className="text-[24px] font-light mb-[16px] group-hover:text-surface">Semantic Sifting</h3>
              <p className="text-[14px] leading-[1.6] opacity-70">Automatically identifies high-entropy nodes in long-form text, discarding filler without losing logical flow.</p>
            </div>
          </div>
          
          {/* Card 2 */}
          <div className="bg-ink text-surface p-[30px] flex flex-col justify-end min-h-[300px] relative overflow-hidden group hover:bg-surface hover:text-ink hover:border hover:border-surface-dim transition-colors duration-300">
            <Database className="absolute top-[30px] right-[30px] w-[32px] h-[32px] opacity-40 group-hover:opacity-100" strokeWidth={1} />
            <div>
              <span className="text-[10px] uppercase tracking-[2px] opacity-60 mb-[8px] block">02</span>
              <h3 className="text-[24px] font-light mb-[16px] group-hover:text-ink">Vector Pruning</h3>
              <p className="text-[14px] leading-[1.6] opacity-70">Optimizes vector space by merging overlapping embeddings into singular high-density representations.</p>
            </div>
          </div>
          
          {/* Card 3 */}
          <div className="bg-surface border border-surface-dim p-[30px] flex flex-col justify-end min-h-[300px] relative overflow-hidden group hover:bg-ink hover:text-surface transition-colors duration-300">
            <Terminal className="absolute top-[30px] right-[30px] w-[32px] h-[32px] opacity-40 group-hover:opacity-100" strokeWidth={1} />
            <div>
              <span className="text-[10px] uppercase tracking-[2px] opacity-60 mb-[8px] block">03</span>
              <h3 className="text-[24px] font-light mb-[16px] group-hover:text-surface">Real-time Inference</h3>
              <p className="text-[14px] leading-[1.6] opacity-70">Compression happens on-the-fly during the pre-fill stage, ensuring no impact on generation speed.</p>
            </div>
          </div>
          
          {/* Card 4 */}
          <div className="bg-ink text-surface p-[30px] flex flex-col justify-end min-h-[300px] relative overflow-hidden group hover:bg-surface hover:text-ink hover:border hover:border-surface-dim transition-colors duration-300">
            <Shield className="absolute top-[30px] right-[30px] w-[32px] h-[32px] opacity-40 group-hover:opacity-100" strokeWidth={1} />
            <div>
              <span className="text-[10px] uppercase tracking-[2px] opacity-60 mb-[8px] block">04</span>
              <h3 className="text-[24px] font-light mb-[16px] group-hover:text-ink">Constraint Extraction</h3>
              <p className="text-[14px] leading-[1.6] opacity-70">Hard-locks mission-critical logic strings while compressing secondary context around them.</p>
            </div>
          </div>
          
          {/* Card 5 */}
          <div className="bg-surface border border-surface-dim p-[30px] flex flex-col justify-end min-h-[300px] relative overflow-hidden group hover:bg-ink hover:text-surface transition-colors duration-300">
            <Waypoints className="absolute top-[30px] right-[30px] w-[32px] h-[32px] opacity-40 group-hover:opacity-100" strokeWidth={1} />
            <div>
              <span className="text-[10px] uppercase tracking-[2px] opacity-60 mb-[8px] block">05</span>
              <h3 className="text-[24px] font-light mb-[16px] group-hover:text-surface">Multi-Model Sync</h3>
              <p className="text-[14px] leading-[1.6] opacity-70">Cross-compatible with Llama, Mistral, and Claude pipelines via unified tensor mapping.</p>
            </div>
          </div>
          
          {/* Card 6 */}
          <div className="bg-ink text-surface p-[30px] flex flex-col justify-end min-h-[300px] relative overflow-hidden group hover:bg-surface hover:text-ink hover:border hover:border-surface-dim transition-colors duration-300">
            <BarChart className="absolute top-[30px] right-[30px] w-[32px] h-[32px] opacity-40 group-hover:opacity-100" strokeWidth={1} />
            <div>
              <span className="text-[10px] uppercase tracking-[2px] opacity-60 mb-[8px] block">06</span>
              <h3 className="text-[24px] font-light mb-[16px] group-hover:text-ink">Token Auditing</h3>
              <p className="text-[14px] leading-[1.6] opacity-70">Detailed read-outs on which specific tokens were reduced and why, providing full audit trails.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

import React from 'react';

export function Footer() {
  return (
    <footer id="docs" className="h-[100px] mx-[60px] border-t border-surface-dim flex flex-col md:flex-row items-center justify-between text-[11px] uppercase tracking-[1px] text-ink-lighter pb-[20px] md:pb-0">
      <div className="flex gap-[60px] w-full md:w-auto justify-between md:justify-start mb-[20px] md:mb-0 mt-[20px] md:mt-0">
        <div className="flex items-center"><b className="text-ink mr-[8px]">04</b> MODULES</div>
        <div className="flex items-center"><b className="text-ink mr-[8px]">10X</b> COMPRESSION</div>
        <div className="hidden md:flex items-center"><b className="text-ink mr-[8px]">00</b> LATENCY</div>
      </div>
      <div>
        &copy; 2024 CONTEXT_COMPRESSION
      </div>
    </footer>
  );
}

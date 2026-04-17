import React from 'react';

export function Navbar() {
  return (
    <nav className="fixed top-0 w-full z-50 bg-background flex justify-between items-center px-[60px] h-[80px] border-b border-surface-dim">
      <div className="font-sans font-black tracking-[2px] uppercase text-ink text-[20px]">
        CONTEXT_COMPRESSION
      </div>
      <div className="hidden md:flex items-center gap-[40px]">
        <a className="font-sans text-[12px] font-medium uppercase text-ink tracking-[1px] hover:opacity-60 transition-opacity" href="#">CAPABILITIES</a>
        <a className="font-sans text-[12px] font-medium uppercase text-ink tracking-[1px] hover:opacity-60 transition-opacity" href="#">ARCHITECTURE</a>
        <a className="font-sans text-[12px] font-medium uppercase text-ink tracking-[1px] hover:opacity-60 transition-opacity" href="#">EVAL_HARNESS</a>
        <a className="font-sans text-[12px] font-medium uppercase text-ink tracking-[1px] opacity-30 hover:opacity-100 transition-opacity" href="#">DOCS</a>
      </div>
      <button className="bg-ink text-surface px-[48px] py-[20px] font-semibold text-[13px] uppercase tracking-[2px] hover:opacity-80 transition-opacity hidden lg:block">
        START BUILDING
      </button>
    </nav>
  );
}

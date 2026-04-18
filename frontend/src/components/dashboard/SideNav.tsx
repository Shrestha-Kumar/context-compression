import { Network, Cpu, Database, List, Power } from "lucide-react";
import { Link } from "react-router-dom";

export function SideNav() {
  return (
    <div className="w-full h-full flex flex-col items-center py-6 md:py-10 justify-between">
      <div className="flex flex-col gap-8 md:gap-10 items-center w-full">
        <Link to="/dashboard" className="group cursor-pointer flex flex-col items-center gap-2 text-white border-r-4 border-white w-full pr-[4px]">
          <Network className="w-5 h-5 md:w-6 md:h-6 group-hover:scale-110 transition-transform duration-200" strokeWidth={2.5} />
        </Link>
        <Link to="/settings" className="group cursor-pointer flex flex-col items-center gap-2 text-[#888] hover:text-white transition-colors w-full">
          <Cpu className="w-5 h-5 md:w-6 md:h-6 group-hover:scale-110 transition-transform duration-200" strokeWidth={2.5} />
        </Link>
        <Link to="/database" className="group cursor-pointer flex flex-col items-center gap-2 text-[#888] hover:text-white transition-colors w-full">
          <Database className="w-5 h-5 md:w-6 md:h-6 group-hover:scale-110 transition-transform duration-200" strokeWidth={2.5} />
        </Link>
        <Link to="/terminal" className="group cursor-pointer flex flex-col items-center gap-2 text-[#888] hover:text-white transition-colors w-full">
          <List className="w-5 h-5 md:w-6 md:h-6 group-hover:scale-110 transition-transform duration-200" strokeWidth={2.5} />
        </Link>
      </div>

      <div className="flex flex-col gap-8 md:gap-10 items-center w-full">
        <Link to="/" className="group cursor-pointer flex flex-col items-center gap-2 text-[#888] hover:text-white transition-colors">
          <Power className="w-5 h-5 md:w-6 md:h-6 group-hover:scale-110 transition-transform duration-200" strokeWidth={2.5} />
        </Link>
        
        {/* Vertical text styling mimicking Kinetic rail-text */}
        <div className="[writing-mode:vertical-rl] rotate-180 uppercase tracking-[0.3em] text-[10px] font-bold text-white whitespace-nowrap hidden md:block">
          AUTUMN / WINTER EDITION
        </div>
      </div>
    </div>
  );
}

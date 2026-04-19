import { Network, MessageSquare, Database, List, Power } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

export function SideNav() {
  const location = useLocation();

  const getIconClass = (path: string, isWhiteBase = false) => {
    // Treat compression and dashboard exactly the same for SideNav highlight
    const isActive = location.pathname === path || (path === '/compression' && location.pathname === '/dashboard');
    if (isActive) {
      return "group cursor-pointer flex flex-col items-center gap-2 text-white border-r-4 border-white w-full pr-[4px]";
    }
    return `group cursor-pointer flex flex-col items-center gap-2 ${isWhiteBase ? 'text-white' : 'text-[#888] hover:text-white'} transition-colors w-full`;
  };

  return (
    <div className="w-full h-full flex flex-col items-center py-6 md:py-10 justify-between">
      <div className="flex flex-col gap-8 md:gap-10 items-center w-full">
        <Link to="/compression" className={getIconClass('/compression', false)}>
          <Network className="w-5 h-5 md:w-6 md:h-6 group-hover:scale-110 transition-transform duration-200" strokeWidth={2.5} />
        </Link>
        <Link to="/sessions" className={getIconClass('/sessions', false)}>
          <MessageSquare className="w-5 h-5 md:w-6 md:h-6 group-hover:scale-110 transition-transform duration-200" strokeWidth={2.5} />
        </Link>
        <Link to="/database" className={getIconClass('/database', false)}>
          <Database className="w-5 h-5 md:w-6 md:h-6 group-hover:scale-110 transition-transform duration-200" strokeWidth={2.5} />
        </Link>
        <Link to="/terminal" className={getIconClass('/terminal', false)}>
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

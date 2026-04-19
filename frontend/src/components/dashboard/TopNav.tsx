import { Settings, Terminal, PanelRight, PanelRightClose } from "lucide-react";
import { useAppStore } from "../../store/appStore";
import { Link, useLocation } from "react-router-dom";

export function TopNav() {
  const { isSidebarVisible, toggleSidebar, currentSessionId } = useAppStore();
  const location = useLocation();

  const getLinkClass = (path: string) => {
    const isActive = location.pathname === path;
    return isActive 
      ? "font-sans text-[11px] font-bold uppercase tracking-[0.2em] text-black border-b-[3px] border-black pb-1"
      : "font-sans text-[11px] font-bold uppercase tracking-[0.2em] text-[#888] hover:text-black transition-colors";
  };

  return (
    <div className="w-full h-full flex justify-between items-center px-6 lg:px-10">
      <div className="flex items-center gap-10">
        <span className="font-sans font-black text-black uppercase tracking-tighter text-2xl lg:text-3xl">
          Kinetic<span className="outline-text">_SYS</span>
        </span>
        <nav className="hidden md:flex gap-8">
          <Link className={getLinkClass('/telemetry')} to="/telemetry">
            TELEMETRY
          </Link>
          <Link className={getLinkClass('/compression')} to="/compression">
            COMPRESSION
          </Link>
          <Link className={getLinkClass('/weights')} to="/weights">
            WEIGHTS
          </Link>
          <Link className={getLinkClass('/latency')} to="/latency">
            LATENCY
          </Link>
        </nav>
      </div>

      <div className="flex items-center gap-6">
        <button onClick={toggleSidebar} className="text-black hover:text-[#888] transition-colors" title="Toggle Layout">
          {isSidebarVisible ? <PanelRightClose className="w-5 h-5" strokeWidth={2.5} /> : <PanelRight className="w-5 h-5" strokeWidth={2.5} />}
        </button>
        <Link to="/terminal" className="hidden lg:flex items-center gap-2 px-3 py-1 bg-[#E0E0E0] hover:bg-black hover:text-[#14F195] border-[2px] border-black font-bold text-[10px] uppercase tracking-widest text-black shadow-[2px_2px_0_#000] transition-colors cursor-pointer" title="Open Terminal">
          <Terminal className="w-3 h-3" strokeWidth={3} />
          SESSION_ID: {currentSessionId ? `0x${currentSessionId.slice(0, 4).toUpperCase()}` : 'NEW_SYS'}
        </Link>
      </div>
    </div>
  );
}

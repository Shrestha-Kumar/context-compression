import { TopNav } from "../components/dashboard/TopNav";
import { SideNav } from "../components/dashboard/SideNav";
import { ArrowLeft, Database as DatabaseIcon } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAppStore } from "../store/appStore";

export default function Database() {
  const navigate = useNavigate();
  const { activeConstraints } = useAppStore();

  const activeTrip = (activeConstraints as any)?.active_trip || {};
  const userProfile = (activeConstraints as any)?.user_profile || {};
  const changelog = (activeConstraints as any)?.changelog || [];

  const formatValue = (value: any): string => {
    if (Array.isArray(value)) return value.map(v => typeof v === 'object' ? JSON.stringify(v) : String(v)).join(', ') || '—';
    if (typeof value === 'object' && value !== null) return JSON.stringify(value);
    return String(value);
  };

  return (
    <div className="h-screen w-screen bg-[#F4F4F2] md:p-6 lg:p-10 box-border flex font-sans overflow-hidden relative text-ink">
      <div className="flex-1 w-full h-full bg-white grid grid-cols-[60px_1fr] md:grid-cols-[80px_1fr] grid-rows-[60px_1fr] md:grid-rows-[80px_1fr] overflow-hidden shadow-2xl">

        {/* Left Rail */}
        <div className="col-start-1 row-start-1 row-span-2 bg-black text-white flex flex-col relative z-20 overflow-hidden">
          <SideNav />
        </div>

        {/* Header */}
        <header className="col-start-2 row-start-1 flex items-center border-[2px] border-black bg-white relative z-10 w-full overflow-hidden mb-[-2px]">
          <TopNav />
        </header>

        {/* Main Content Areas */}
        <main className="col-start-2 row-start-2 flex overflow-hidden border-[3px] border-black border-t-0 relative flex-col font-mono text-ink bg-surface-dim">
          <div className="flex items-center justify-between border-b-[3px] border-black pb-4 pt-6 px-8 lg:px-12 bg-white shrink-0">
            <button 
              onClick={() => navigate('/dashboard')}
              className="group flex items-center gap-3 font-black text-xl lg:text-3xl uppercase tracking-tighter hover:text-[#888] transition-colors"
            >
              <ArrowLeft className="w-8 h-8 group-hover:-translate-x-1 transition-transform" strokeWidth={4} />
              Database <span className="outline-text">_PERSIST</span>
            </button>
            <DatabaseIcon className="w-8 h-8 text-black animate-pulse" strokeWidth={2.5} />
          </div>

          <div className="flex-1 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-[3px] bg-black p-[3px] overflow-hidden">
            
            {/* Active Trip Data */}
            <div className="bg-white flex flex-col overflow-hidden">
              <div className="h-10 bg-black text-white flex items-center px-4 font-black text-[10px] uppercase tracking-[0.3em] border-b-[3px] border-black shrink-0">
                ACTIVE_TRIP_MEMORY
              </div>
              <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
                {Object.keys(activeTrip).length === 0 ? (
                  <div className="h-full flex items-center justify-center text-[10px] text-[#888] font-black tracking-widest uppercase animate-pulse">
                    [ NO_ACTIVE_DATAPOINTS ]
                  </div>
                ) : (
                  Object.entries(activeTrip).map(([key, value], i) => (
                    <div key={key} className="border-l-[4px] border-black pl-4 py-2 hover:bg-[#F8F8F8] transition-colors group">
                      <span className="block text-[9px] text-[#888] uppercase tracking-[0.2em] font-black mb-1.5 group-hover:text-black transition-colors">{key}</span>
                      <span className="block text-[14px] font-black break-words leading-tight uppercase tracking-tighter">{formatValue(value)}</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* User Profile Implicit Knowledge */}
            <div className="bg-white flex flex-col overflow-hidden border-l-[3px] border-black">
              <div className="h-10 bg-black text-[#14F195] flex items-center px-4 font-black text-[10px] uppercase tracking-[0.3em] border-b-[3px] border-[#14F195]/30 shrink-0">
                USER_PROFILE_KNOWLEDGE
              </div>
              <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-8">
                <div>
                  <span className="block text-[10px] text-[#888] uppercase tracking-[0.2em] font-black mb-4 border-b-[2px] border-black pb-2">Routines</span>
                  {(!userProfile.routines || userProfile.routines.length === 0) ? (
                    <div className="text-[10px] text-[#888] font-black uppercase tracking-[0.2em]">[ NO_ROUTINES_LEARNED ]</div>
                  ) : (
                    (userProfile.routines as string[]).map((r, i) => (
                      <div key={i} className="mb-3 border-[2px] border-black p-4 bg-white shadow-[4px_4px_0_#000] hover:translate-x-1 hover:-translate-y-1 transition-transform cursor-default">
                        <span className="text-[12px] font-black uppercase tracking-tight">{r}</span>
                      </div>
                    ))
                  )}
                </div>

                <div>
                  <span className="block text-[10px] text-[#888] uppercase tracking-[0.2em] font-black mb-4 border-b-[2px] border-black pb-2">Preferences</span>
                  {(!userProfile.preferences || userProfile.preferences.length === 0) ? (
                    <div className="text-[10px] text-[#888] font-black uppercase tracking-[0.2em]">[ NO_PREFERENCES_SET ]</div>
                  ) : (
                    (userProfile.preferences as string[]).map((p, i) => (
                      <div key={i} className="mb-3 border-[2px] border-black p-4 bg-black text-white shadow-[4px_4px_0_#14F195] hover:translate-x-1 hover:-translate-y-1 transition-transform cursor-default">
                        <span className="text-[12px] font-black uppercase tracking-tight text-[#14F195]">{p}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Changelog History */}
            <div className="bg-[#111] flex flex-col overflow-hidden lg:col-span-1 md:col-span-2 border-l-[3px] border-black">
              <div className="h-10 bg-black text-[#14F195] flex items-center px-6 font-black text-[10px] uppercase tracking-[0.3em] border-b-[3px] border-[#14F195] shrink-0">
                AUDIT_TRAIL (TEMPORAL)
              </div>
              <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4">
                {(!changelog || changelog.length === 0) ? (
                  <div className="h-full flex items-center justify-center text-[10px] text-[#888] font-black tracking-widest uppercase">
                    [ NO_CHANGES_LOGGED ]
                  </div>
                ) : (
                  changelog.map((log: any, i: number) => {
                    const actionLower = (log.action || '').toLowerCase();
                    const isDelete = actionLower.includes('delete') || actionLower.includes('remove');
                    const accent = isDelete ? 'border-red-500' : 'border-[#14F195]';
                    return (
                      <div key={i} className={`border-l-[6px] ${accent} bg-black p-4 text-white hover:bg-[#111] transition-all hover:translate-x-1 shadow-[4px_4px_0_#000]`}>
                        <div className="flex justify-between items-center mb-2">
                          <span className="block text-[8px] tracking-[0.2em] uppercase font-black opacity-40">
                            {log.date || 'SYS_DATE_UNAVAILABLE'}
                          </span>
                          <span className={`text-[8px] font-black uppercase tracking-widest px-1.5 py-0.5 ${isDelete ? 'bg-red-500/20 text-red-500' : 'bg-[#14F195]/20 text-[#14F195]'}`}>
                            {isDelete ? 'D' : 'C'}
                          </span>
                        </div>
                        <span className="text-[13px] font-black leading-tight uppercase tracking-tight">{log.action}</span>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

          </div>
        </main>
      </div>
    </div>
  );
}

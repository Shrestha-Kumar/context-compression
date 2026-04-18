import { useAppStore } from "../../store/appStore";

export function ConstraintsSidebar() {
  const { activeConstraints } = useAppStore();

  const activeTrip = activeConstraints?.active_trip || {};
  const userProfile = activeConstraints?.user_profile || {};
  const changelog = activeConstraints?.changelog || [];

  return (
    <aside className="w-[300px] bg-background p-8 flex flex-col gap-6 h-full overflow-y-auto no-scrollbar hidden md:flex shrink-0 cursor-grab active:cursor-grabbing">
      <div className="flex flex-col gap-6">
        
        {/* Active Trip Section */}
        <section>
          <span className="font-bold text-[10px] text-ink uppercase tracking-[0.2em] border-b border-surface-dim pb-3 block mb-4">
            Active Trip Memory
          </span>
          <div className="flex flex-col gap-3">
            {Object.keys(activeTrip).length === 0 ? (
              <div className="text-[10px] text-[#888] font-mono p-4 border border-surface-dim uppercase text-center opacity-50">
                [NO ACTIVE TRIP DATA]
              </div>
            ) : (
              Object.entries(activeTrip).map(([key, value], i) => (
                <div key={`trip-${i}`} className="flex flex-col gap-1 border border-surface-dim p-2 bg-surface shadow-sm">
                  <span className="font-bold text-[8px] text-[#888] uppercase tracking-[0.2em]">{key}</span>
                  <span className="text-[11px] font-bold text-ink uppercase break-words">
                    {Array.isArray(value) ? value.map(v => typeof v === 'object' ? JSON.stringify(v) : v).join(', ') : JSON.stringify(value)}
                  </span>
                </div>
              ))
            )}
          </div>
        </section>

        {/* User Profile Section */}
        <section>
          <span className="font-bold text-[10px] text-ink uppercase tracking-[0.2em] border-b border-surface-dim pb-3 block mb-4 mt-2">
            Global User Profile
          </span>
          <div className="flex flex-col gap-3">
            {Object.keys(userProfile).length === 0 ? (
              <div className="text-[10px] text-[#888] font-mono p-4 border border-surface-dim uppercase text-center opacity-50">
                [NO IMPLICIT KNOWLEDGE]
              </div>
            ) : (
              Object.entries(userProfile).map(([key, value], i) => (
                <div key={`prof-${i}`} className="flex flex-col gap-1 border border-surface-dim p-2 bg-surface shadow-sm">
                  <span className="font-bold text-[8px] text-[#888] uppercase tracking-[0.2em]">{key}</span>
                  <span className="text-[11px] font-bold text-ink uppercase break-words">
                    {Array.isArray(value) ? value.join(', ') : JSON.stringify(value)}
                  </span>
                </div>
              ))
            )}
          </div>
        </section>

        {/* Temporal Changelog */}
        <section>
          <span className="font-bold text-[10px] text-[red] uppercase tracking-[0.2em] border-b border-surface-dim pb-3 block mb-4 mt-2">
            CRU/D Temporal Audit
          </span>
          <div className="flex flex-col gap-2">
            {!Array.isArray(changelog) || changelog.length === 0 ? (
              <div className="text-[10px] text-[#888] font-mono p-4 border border-surface-dim uppercase text-center opacity-50">
                [NO ACTIONS LOGGED]
              </div>
            ) : (
              changelog.map((log: any, i: number) => (
                <div key={`log-${i}`} className="flex flex-col border border-surface-dim p-2 bg-surface">
                  <span className="font-bold text-[8px] text-[red] tracking-[0.2em]">{log.date || "NO_DATE"}</span>
                  <span className="text-[9px] font-mono text-ink mt-1 uppercase break-words">→ {log.action}</span>
                </div>
              ))
            )}
          </div>
        </section>

      </div>

      <div className="mt-auto pt-8 flex flex-col gap-4">
        <button 
          onClick={async () => {
             const res = await fetch('http://localhost:8000/generate_summary', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_profile: userProfile, changelog: changelog })
             });
             const data = await res.json();
             // Simple hackathon download to text
             const blob = new Blob([data.summary], { type: 'text/markdown' });
             const url = URL.createObjectURL(blob);
             const a = document.createElement('a');
             a.href = url;
             a.download = 'User_Profile_Summary.md';
             a.click();
          }}
          className="bg-[rgba(255,0,0,0.1)] text-[red] text-[8px] font-black py-3 uppercase tracking-[0.2em] border border-[rgba(255,0,0,0.2)] hover:bg-[red] hover:text-white transition-all shadow-sm">
          Export MD Summary
        </button>
        <button 
          onClick={() => window.location.reload()}
          className="bg-ink text-surface text-[10px] font-black py-4 uppercase tracking-[0.2em] hover:bg-background hover:text-ink border border-surface-dim transition-all shadow-sm">
          Re-sync State
        </button>
      </div>
    </aside>
  );
}

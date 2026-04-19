import { useAppStore } from "../../store/appStore";

export function ConstraintsSidebar() {
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
    <aside className="w-[340px] shrink-0 bg-background flex flex-col h-full border-l border-surface-dim overflow-hidden">

      {/* Header — matches MetricsPanel height exactly */}
      <div className="h-16 flex items-center border-b border-surface-dim px-6 shrink-0">
        <span className="font-black text-[11px] uppercase tracking-[0.2em] text-ink">Memory_STATE</span>
      </div>

      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto no-scrollbar flex flex-col gap-0">

        {/* ─── Active Trip ──────────────────────────────── */}
        <section className="p-5 border-b border-surface-dim">
          <span className="font-bold text-[13px] font-black uppercase tracking-[0.25em] block mb-3">
            Active Trip Memory
          </span>
          <div className="flex flex-col gap-2">
            {Object.keys(activeTrip).length === 0 ? (
              <div className="text-[11px] text-[#888] font-mono uppercase text-center py-3 border border-dashed border-surface-dim">
                No active trip data
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {activeTrip.destinations && activeTrip.destinations.length > 0 && (
                  <div className="border-b border-surface-dim pb-2 group">
                    <span className="text-[9px] text-[#888] font-black uppercase tracking-[0.2em] block mb-1">Destinations</span>
                    <span className="text-[12px] font-black uppercase tracking-tighter text-ink block break-words leading-tight">
                      {activeTrip.destinations.join(', ')}
                    </span>
                  </div>
                )}
                
                {activeTrip.dates && (activeTrip.dates.start || activeTrip.dates.end) && (
                  <div className="border-b border-surface-dim pb-2 group">
                    <span className="text-[9px] text-[#888] font-black uppercase tracking-[0.2em] block mb-1">Schedule</span>
                    <span className="text-[12px] font-black uppercase tracking-tighter text-ink block">
                      {activeTrip.dates.start || 'TBD'} → {activeTrip.dates.end || 'TBD'}
                    </span>
                  </div>
                )}

                {activeTrip.budget && (
                  <div className="border-b border-surface-dim pb-2 group flex justify-between items-center">
                    <span className="text-[9px] text-[#888] font-black uppercase tracking-[0.2em]">Budget Cap</span>
                    <span className="text-[12px] font-black uppercase tracking-tighter text-ink">${activeTrip.budget}</span>
                  </div>
                )}

                {activeTrip.bookings && activeTrip.bookings.length > 0 && (
                  <div className="border-b border-surface-dim pb-2 group">
                    <span className="text-[9px] text-[#888] font-black uppercase tracking-[0.2em] block mb-1">Active Bookings</span>
                    <div className="flex flex-col gap-1">
                      {activeTrip.bookings.map((b: any, i: number) => (
                        <div key={i} className="text-[11px] font-black uppercase tracking-tighter text-ink flex justify-between">
                          <span>{b.type || 'Booking'}</span>
                          <span className="text-[#888]">{b.code || '—'}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </section>

        {/* ─── Routines ───────────────────────────────── */}
        <section className="p-5 border-b border-surface-dim">
          <span className="font-bold text-[13px] font-black uppercase tracking-[0.25em] block mb-3">
            Routines
          </span>
          <div className="flex flex-col gap-2">
            {(!userProfile.routines || userProfile.routines.length === 0) ? (
              <div className="text-[11px] text-[#888] font-mono uppercase text-center py-3 border border-dashed border-surface-dim">
                No routines learned
              </div>
            ) : (
              (userProfile.routines as string[]).map((r, i) => (
                <div key={`r-${i}`} className="border-l-[3px] border-ink pl-3 py-1">
                  <span className="text-[12px] font-black text-ink uppercase break-words leading-snug">{r}</span>
                </div>
              ))
            )}
          </div>
        </section>

        {/* ─── Preferences ───────────────────────────── */}
        <section className="p-5 border-b border-surface-dim">
          <span className="font-bold text-[13px] font-black uppercase tracking-[0.25em] block mb-3">
            Preferences
          </span>
          <div className="flex flex-col gap-2">
            {(!userProfile.preferences || userProfile.preferences.length === 0) ? (
              <div className="text-[11px] text-[#888] font-mono uppercase text-center py-3 border border-dashed border-surface-dim">
                No preferences learned
              </div>
            ) : (
              (userProfile.preferences as string[]).map((p, i) => (
                <div key={`p-${i}`} className="border-l-[3px] border-surface-dim pl-3 py-1">
                  <span className="text-[12px] font-black text-ink uppercase break-words leading-snug">{p}</span>
                </div>
              ))
            )}
          </div>
        </section>

        {/* ─── CRU/D Temporal Audit ──────────────────── */}
        <section className="p-5 flex-1">
          <span className="font-bold text-[9px] uppercase tracking-[0.25em] block mb-3 text-ink">
            CRU/D Temporal Audit
          </span>
          <div className="flex flex-col gap-2">
            {!Array.isArray(changelog) || changelog.length === 0 ? (
              <div className="text-[11px] text-[#888] font-mono uppercase text-center py-3 border border-dashed border-surface-dim">
                [No actions logged]
              </div>
            ) : (
              changelog.map((log: any, i: number) => {
                const actionLower = (log.action || '').toLowerCase();
                const isDelete = actionLower.includes('delete') || actionLower.includes('remove') || actionLower.includes('cancel');
                const isUpdate = actionLower.includes('update') || actionLower.includes('change') || actionLower.includes('modify');
                const accentColor = isDelete ? '#cc0000' : isUpdate ? '#777' : '#1A1A1A';
                return (
                  <div key={`log-${i}`} className="flex flex-col border-l-[3px] pl-3 py-1" style={{ borderColor: accentColor }}>
                    <span className="font-bold text-[10px] tracking-[0.2em] uppercase" style={{ color: accentColor }}>
                      {log.date || 'NO_DATE'}
                    </span>
                    <span className="text-[9px] font-mono text-ink mt-[2px] break-words leading-snug">
                      → {log.action}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </section>

      </div>

      {/* ─── Action Buttons ───────────────────────────── */}
      <div className="shrink-0 border-t border-surface-dim flex flex-col">
        <button
          onClick={async (e) => {
            const btn = e.currentTarget;
            const originalText = btn.innerText;
            btn.innerText = 'GENERATING...';
            btn.disabled = true;
            try {
              const res = await fetch('http://localhost:8000/generate_summary', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  memory: activeConstraints,
                  user_profile: userProfile,
                  active_trip: activeTrip,
                  changelog: changelog
                })
              });
              if (!res.ok) throw new Error('Backend export failed');
              const data = await res.json();
              if (!data.summary) throw new Error('Empty summary returned');
              const blob = new Blob([data.summary], { type: 'text/markdown' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `Kinetic_SYS_Profile_${new Date().toISOString().split('T')[0]}.md`;
              a.click();
              URL.revokeObjectURL(url);
            } catch (err) {
              console.error(err);
              alert('Export failed. Check backend connectivity.');
            } finally {
              btn.innerText = originalText;
              btn.disabled = false;
            }
          }}
          className="w-full py-3 text-[10px] font-black uppercase tracking-[0.2em] bg-surface-dim text-ink hover:bg-ink hover:text-surface transition-colors border-b border-surface-dim disabled:opacity-50"
        >
          Export MD Summary
        </button>
        <button
          onClick={() => window.location.reload()}
          className="w-full py-3 text-[10px] font-black uppercase tracking-[0.2em] bg-ink text-surface hover:bg-[#333] transition-colors"
        >
          Re-sync State
        </button>
      </div>

    </aside>
  );
}

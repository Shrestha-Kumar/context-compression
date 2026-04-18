import { useAppStore } from "../../store/appStore";

export function ConstraintsSidebar() {
  const { activeConstraints } = useAppStore();

  return (
    <aside className="w-[260px] bg-background p-8 flex flex-col gap-6 h-full overflow-y-auto no-scrollbar hidden md:flex shrink-0 cursor-grab active:cursor-grabbing">
      <span className="font-bold text-[10px] text-ink uppercase tracking-[0.2em] border-b border-surface-dim pb-3">
        Active Constraints
      </span>
      
      <div className="flex flex-col gap-5">
        {Object.entries(activeConstraints).length === 0 ? (
          <div className="text-[10px] text-[#888] font-mono p-4 border border-surface-dim uppercase text-center opacity-50">
            [AWAITING INFERENCE]
          </div>
        ) : (
          Object.entries(activeConstraints).map(([key, value], i) => (
          <div key={i} className="flex flex-col gap-2 border border-surface-dim p-3 bg-surface shadow-sm">
            <span className="font-bold text-[8px] text-[#888] uppercase tracking-[0.2em] overflow-hidden text-ellipsis whitespace-nowrap">
              {key}
            </span>
            <span className="text-[11px] font-bold text-ink break-words leading-tight uppercase">
              {Array.isArray(value) 
                ? (value.length > 0 && typeof value[0] === 'object' 
                    ? value.map(v => v.name || v.flight_code || JSON.stringify(v)).join(', ') 
                    : value.join(', '))
                : (typeof value === 'object' ? JSON.stringify(value) : String(value))}
            </span>
          </div>
          ))
        )}
      </div>

      <div className="mt-auto pt-8 border-t border-surface-dim flex flex-col gap-6">
        <div className="flex flex-col gap-3">
          <span className="font-bold text-[8px] text-[#888] uppercase tracking-[0.2em]">
            System Integrity
          </span>
          <div className="flex gap-2 p-2 border border-surface-dim bg-surface">
            <div className="h-2 flex-1 bg-ink"></div>
            <div className="h-2 flex-1 bg-ink"></div>
            <div className="h-2 flex-1 bg-ink"></div>
            <div className="h-2 flex-1 bg-background"></div>
          </div>
        </div>
        <button 
          onClick={() => window.location.reload()}
          className="bg-ink text-surface text-[10px] font-black py-4 uppercase tracking-[0.2em] hover:bg-background hover:text-ink border border-surface-dim transition-all shadow-sm">
          Re-sync State
        </button>
      </div>
    </aside>
  );
}

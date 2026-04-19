import { TopNav } from "../components/dashboard/TopNav";
import { SideNav } from "../components/dashboard/SideNav";
import { ChatPanel } from "../components/dashboard/ChatPanel";
import { MetricsPanel } from "../components/dashboard/MetricsPanel";
import { ConstraintsSidebar } from "../components/dashboard/ConstraintsSidebar";
import React, { useState, useCallback, useRef, useEffect } from "react";
import { AnimatePresence, motion } from "motion/react";
import { useAppStore } from "../store/appStore";
import { useSearchParams } from "react-router-dom";

const DEFAULT_METRICS_WIDTH = 420;
const MIN_METRICS_WIDTH = 300;
const MAX_METRICS_WIDTH = 700;

export default function Dashboard() {
  const [searchParams] = useSearchParams();
  const sessionIdFromUrl = searchParams.get('session_id');
  const { isSidebarVisible, currentSessionId, setCurrentSessionId, setMessages, updateConstraints, updateMetrics } = useAppStore();
  
  const [metricsCollapsed, setMetricsCollapsed] = useState(false);
  const [metricsWidth, setMetricsWidth] = useState(DEFAULT_METRICS_WIDTH);
  const dragging = useRef(false);
  const startX = useRef(0);
  const startWidth = useRef(DEFAULT_METRICS_WIDTH);

  // Handle Session Restoration
  useEffect(() => {
    if (sessionIdFromUrl && sessionIdFromUrl !== currentSessionId) {
      setCurrentSessionId(sessionIdFromUrl);
      
      // Fetch session data from backend
      fetch(`http://localhost:8000/sessions/${sessionIdFromUrl}`)
        .then(res => res.json())
        .then(data => {
          if (!data.error) {
            // Restore messages (mapping from turn_number format to ChatPanel format)
            const restoredMessages = (data.messages || []).map((m: any, i: number) => ({
              id: `#0${i}`,
              text: m.data?.content || m.content, // Handling both raw and LangChain serialized formats
              isUser: m.type === 'human' || m.role === 'human',
              tokens: m.role === 'human' ? '' : '↓ RESTORED'
            }));
            
            setMessages(restoredMessages);
            if (data.memory) updateConstraints(data.memory);
            
            // Restore latest metrics if available
            if (data.compression_history && data.compression_history.length > 0) {
              const latest = data.compression_history[data.compression_history.length - 1];
              updateMetrics({
                compRatio: latest.ratio || 0,
                tokens: latest.compressed_tokens || 0,
                turn: `#0${latest.turn_number || 0}`,
                raw_tokens: latest.raw_tokens || 0,
                compressed_tokens: latest.compressed_tokens || 0
              });
            } else {
              // Reset if no history
              updateMetrics({ compRatio: 0, tokens: 0, turn: "#00", raw_tokens: 0, compressed_tokens: 0 });
            }
          }
        })
        .catch(err => console.error("Restoration failed:", err));
    }
  }, [sessionIdFromUrl, currentSessionId, setCurrentSessionId, setMessages, updateConstraints]);

  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    dragging.current = true;
    startX.current = e.clientX;
    startWidth.current = metricsWidth;

    const onMove = (ev: MouseEvent) => {
      if (!dragging.current) return;
      const delta = ev.clientX - startX.current;
      const next = Math.min(MAX_METRICS_WIDTH, Math.max(MIN_METRICS_WIDTH, startWidth.current + delta));
      setMetricsWidth(next);
    };
    const onUp = () => {
      dragging.current = false;
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    e.preventDefault();
  }, [metricsWidth]);

  return (
    <div className="h-screen w-screen bg-[#F4F4F2] md:p-6 lg:p-10 box-border flex font-sans overflow-hidden relative text-ink">
      <div className="flex-1 w-full h-full bg-white grid grid-cols-[60px_1fr] md:grid-cols-[80px_1fr] grid-rows-[60px_1fr] md:grid-rows-[80px_1fr] overflow-hidden relative shadow-2xl">

        {/* Left Rail */}
        <div className="col-start-1 row-start-1 row-span-2 bg-black text-white flex flex-col relative z-20 overflow-hidden">
          <SideNav />
        </div>

        {/* Header */}
        <header className="col-start-2 row-start-1 border-b-[2px] border-black bg-white flex items-center relative z-10 w-full overflow-hidden">
          <TopNav />
        </header>

        {/* Main Content Area */}
        <main className="col-start-2 row-start-2 flex overflow-hidden bg-white w-full">
          <ChatPanel />

          <AnimatePresence>
            {isSidebarVisible && (
              <motion.div
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: metricsCollapsed ? 380 : (metricsWidth + 340), opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="flex overflow-hidden shrink-0 border-l-[2px] border-black h-full"
                style={{ userSelect: dragging.current ? 'none' : 'auto' }}
              >
                {/* Metrics panel (collapsible + resizable) */}
                <MetricsPanel
                  collapsed={metricsCollapsed}
                  onToggleCollapse={() => setMetricsCollapsed(c => !c)}
                  width={metricsCollapsed ? 40 : metricsWidth}
                  onResizeStart={handleResizeStart}
                />

                {/* Memory state sidebar */}
                <ConstraintsSidebar />
              </motion.div>
            )}
          </AnimatePresence>
        </main>

        {/* Geometric flair */}
        <div className="absolute bottom-[-10px] right-[280px] w-24 h-24 bg-black z-50 pointer-events-none hidden lg:block shadow-[10px_10px_0_#ccc]" />
      </div>
    </div>
  );
}

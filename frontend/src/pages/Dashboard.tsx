import { TopNav } from "../components/dashboard/TopNav";
import { SideNav } from "../components/dashboard/SideNav";
import { ChatPanel } from "../components/dashboard/ChatPanel";
import { MetricsPanel } from "../components/dashboard/MetricsPanel";
import { ConstraintsSidebar } from "../components/dashboard/ConstraintsSidebar";
import { useState } from "react";
import { Reorder, AnimatePresence, motion } from "motion/react";
import { useAppStore } from "../store/appStore";

export default function Dashboard() {
  const [panels, setPanels] = useState(['metrics', 'constraints']);
  const isSidebarVisible = useAppStore((state) => state.isSidebarVisible);

  return (
    <div className="h-screen w-screen bg-[#F4F4F2] md:p-6 lg:p-10 box-border flex font-sans overflow-hidden relative text-ink">
      {/* Main Container without borders */}
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
                animate={{ width: "auto", opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                className="flex flex-1 overflow-hidden pointer-events-none"
              >
                <Reorder.Group axis="x" values={panels} onReorder={setPanels} className="flex flex-1 overflow-hidden pointer-events-auto">
                  {panels.map((panel) => (
                    <Reorder.Item 
                      key={panel} 
                      value={panel} 
                      className={`h-full flex shrink-0 ${panel === 'metrics' ? 'flex-1 min-w-[360px]' : 'w-[260px]'}`}
                    >
                      {panel === 'metrics' ? <MetricsPanel /> : <ConstraintsSidebar />}
                    </Reorder.Item>
                  ))}
                </Reorder.Group>
              </motion.div>
            )}
          </AnimatePresence>
        </main>
        
        {/* Floating Geometric Element for Flair */}
        <div className="absolute bottom-[-10px] right-[280px] w-24 h-24 bg-black z-50 pointer-events-none hidden lg:block shadow-[10px_10px_0_#ccc]"></div>
      </div>
    </div>
  );
}

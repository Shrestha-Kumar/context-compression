import { TopNav } from "../components/dashboard/TopNav";
import { SideNav } from "../components/dashboard/SideNav";
import { useAppStore } from "../store/appStore";

export default function Telemetry() {
  const { messages, metrics, wsConnected } = useAppStore();

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

        {/* Main Content */}
        <main className="col-start-2 row-start-2 flex overflow-hidden border-[3px] border-black border-t-0 p-8 lg:p-12 relative flex-col gap-8 font-mono text-ink bg-white">
          <div className="flex items-center justify-between border-b-[3px] border-black pb-6">
            <h1 className="font-black text-2xl lg:text-3xl uppercase tracking-tighter">
              Datalink <span className="outline-text">Stream</span>
            </h1>
            <div className="flex items-center gap-6">
              <div className="flex flex-col items-end">
                <span className="text-[10px] font-black text-[#888] uppercase tracking-[0.2em]">Active Connection</span>
                <span className={`text-[12px] font-black uppercase tracking-[0.2em] px-3 py-1 bg-black ${wsConnected ? 'text-[#14F195]' : 'text-red-500'}`}>
                  {wsConnected ? 'SECURE_WSS_ALIVE' : 'DATALINK_DROPPED'}
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 shrink-0">
            <div className="border-[3px] border-black p-6 bg-white shadow-[6px_6px_0_#000]">
              <p className="text-[10px] text-[#888] uppercase tracking-[0.1em] font-black mb-2">Ingested Messages</p>
              <p className="text-3xl font-black tracking-tighter">{messages.length}</p>
            </div>
            <div className="border-[3px] border-black p-6 bg-white shadow-[6px_6px_0_#000]">
              <p className="text-[10px] text-[#888] uppercase tracking-[0.1em] font-black mb-2">Extracted Tokens</p>
              <p className="text-3xl font-black tracking-tighter">{metrics.tokens}</p>
            </div>
            <div className="border-[3px] border-black p-6 bg-black text-[#14F195] shadow-[6px_6px_0_#333]">
              <p className="text-[10px] text-[#888] uppercase tracking-[0.1em] font-black mb-2">Context Turn</p>
              <p className="text-3xl font-black tracking-tighter">{metrics.turn}</p>
            </div>
          </div>

          <div className="flex-1 border-[3px] border-black mt-2 relative overflow-hidden bg-background flex flex-col shadow-[10px_10px_0_#000]">
            <div className="h-10 bg-black text-[#14F195] flex items-center px-6 font-black text-[10px] uppercase tracking-[0.3em] justify-between shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-1.5 h-1.5 bg-[#14F195] animate-ping" />
                <span>RAW_WEBSOCKET_FEED</span>
              </div>
              <span className="opacity-50 text-[9px]">127.0.0.1:8000</span>
            </div>
            <div className="p-6 flex-1 overflow-y-auto no-scrollbar space-y-6 bg-white">
              {messages.length === 0 ? (
                <div className="h-full flex items-center justify-center text-[#888] text-[10px] font-black uppercase tracking-[0.5em] animate-pulse">
                  [ AWAITING_INGESTION ... ]
                </div>
              ) : (
                messages.map((msg, i) => (
                  <div key={i} className="flex gap-6 border-l-[3px] border-black pl-5 py-1.5 hover:bg-[#F8F8F8] transition-colors">
                    <div className="w-[120px] shrink-0 flex flex-col gap-1">
                      <span className="text-[9px] text-[#888] font-black uppercase tracking-widest">
                        {new Date().toISOString().split('T')[1].split('.')[0]}
                      </span>
                      <span className={`text-[10px] font-black uppercase tracking-tighter ${msg.isUser ? 'text-black' : 'text-blue-600'}`}>
                        {msg.isUser ? '→ USER_INPUT' : '← SYS_REPLY'}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[14px] font-black text-ink break-words leading-tight">{msg.text}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-[9px] bg-black text-white px-1.5 py-0.5 font-black uppercase tracking-widest">TOK: {msg.tokens}</span>
                        <div className="flex-1 h-[1px] bg-surface-dim" />
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

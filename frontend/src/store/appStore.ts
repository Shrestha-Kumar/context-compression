import { create } from 'zustand';

export interface ChatMessage {
  id: string;
  tokens: string;
  text: string;
  isUser: boolean;
}

export interface TokenScore {
  text: string;
  score: number;
  preserved: boolean;
  is_entity: boolean;
}

export interface KVCacheMetrics {
  evicted_count: number;
  window_size: number;
}

interface AppState {
  isTransitioning: boolean;
  targetRoute: string | null;
  startTransition: (route: string) => void;
  endTransition: () => void;

  messages: ChatMessage[];
  appendMessage: (msg: ChatMessage) => void;
  setMessages: (msgs: ChatMessage[]) => void;

  currentSessionId: string | null;
  setCurrentSessionId: (id: string | null) => void;

  metrics: {
    compRatio: number;
    tokens: number;
    turn: string;
    vram_mb: number;
    raw_tokens: number;
    compressed_tokens: number;
  };
  updateMetrics: (m: Partial<AppState['metrics']>) => void;

  activeConstraints: Record<string, string>;
  updateConstraints: (constraints: Record<string, string>) => void;

  tokenHeatmap: TokenScore[];
  updateTokenHeatmap: (heatmap: TokenScore[]) => void;

  kvCacheMetrics: KVCacheMetrics | null;
  updateKVCache: (metrics: KVCacheMetrics) => void;

  wsConnected: boolean;
  setWsConnected: (status: boolean) => void;

  sendMessage: (text: string) => void;
  _setSendMessage: (fn: (text: string) => void) => void;

  isSidebarVisible: boolean;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  isTransitioning: false,
  targetRoute: null,
  startTransition: (route) => set({ isTransitioning: true, targetRoute: route }),
  endTransition: () => set({ isTransitioning: false, targetRoute: null }),

  messages: [],
  appendMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setMessages: (msgs) => set({ messages: msgs }),

  currentSessionId: null,
  setCurrentSessionId: (id) => set({ currentSessionId: id }),

  metrics: { compRatio: 0, tokens: 0, turn: "#00", vram_mb: 0, raw_tokens: 0, compressed_tokens: 0 },
  updateMetrics: (m) => set((state) => ({ metrics: { ...state.metrics, ...m } })),

  activeConstraints: {},
  updateConstraints: (constraints) => set({ activeConstraints: constraints }),

  tokenHeatmap: [],
  updateTokenHeatmap: (heatmap) => set({ tokenHeatmap: heatmap }),

  kvCacheMetrics: null,
  updateKVCache: (metrics) => set({ kvCacheMetrics: metrics }),

  wsConnected: false,
  setWsConnected: (status) => set({ wsConnected: status }),

  sendMessage: () => {},
  _setSendMessage: (fn) => set({ sendMessage: fn }),

  isSidebarVisible: true,
  toggleSidebar: () => set((state) => ({ isSidebarVisible: !state.isSidebarVisible })),
}));

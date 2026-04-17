# Architecture for Context Compression Module Frontend

## Goal Description
Build a React + Next.js 14 (App Router) demo frontend for a "Context Compression Module", connecting to an existing local Python FastAPI server via WebSocket (`ws://localhost:8000/ws`). The UI is a 60/40 split pane focusing on showcasing context compression telemetry (metrics, token heatmaps, KV-cache visualizations).

## Proposed Changes
1. **Next.js Scaffold:** Create a Next.js 14 app under `frontend/` with TS and Tailwind.
2. **Library Additions:** Install `shadcn/ui`, `framer-motion`, `recharts`, `lucide-react`, and `zustand`.
3. **Core Elements:**
   - **WebSocket Integration:** `hooks/useWebSocket.ts` to manage WS state based on the exact definitions in `contracts/ws_schema.py`. It'll drive UI updates through `zustand` (`store/appStore.ts`).
   - **Split Layout (`app/page.tsx`):** A fixed single-page design.
   - **ChatPane (Left - 40%):** Message history (User, Assistant, Tools), input field with thinking states, and starter suggestion list.
   - **DebuggerPane (Right - 60%):** Tabbed interface with `MetricsTab` (Recharts KPI), `TokenHeatmapTab` (color-coded tokens based on TF-IDF), and `KVCacheTab` (sliding window of prompt tokens). Includes a persistent `ConstraintSidebar`.

## Verification Plan
### Automated Tests
* None specified, but `npm run lint` and `npm run build` will verify TypeScript soundness.

### Manual Verification
1. Boot Next.js via `npm run dev` and python backend via `/backend/app.py`.
2. Connect to local WebSocket `ws://localhost:8000/ws` and observe telemetry matching `contracts/ws_schema.py`.
3. Test layout sizing, CSS themes (dark mode default), and visual presentation of KPI blocks and the Token Heatmap token coloring constraints (score thresholding logic).

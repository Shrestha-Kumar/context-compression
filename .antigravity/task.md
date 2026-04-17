# Context Compression Module - Frontend Development

## Planning
- [x] Review existing files (contracts, README, SVG, requirements.txt)
- [x] Verify micromamba environments ("dl" env specifically) and Python dependencies
- [x] Evaluate user-uploaded Vite + React landing page design

## Scaffold & Setup
- [x] Initialize Vite + React project (detected from AI Studio design)
- [x] Integrate Spline component with parallax and sticky background layers
- [ ] Configure design tokens (dark mode, colors, typography)
- [ ] Setup `ws_schema.ts` based on backend contract
- [ ] Implement `useWebSocket` hook with Zustand store slice

## Component Development
- [ ] Implement Layout (Split View 60/40)
- [ ] Build ChatPane (Left Pane 40%)
  - [ ] Message feed (user, assistant, tool calls)
  - [ ] Input box with "thinking..." indicator
  - [ ] Starter suggestions panel
- [ ] Build ConstraintSidebar (Right Pane - Fixed)
  - [ ] Dictionary visualization with pulse animations
- [ ] Build DebuggerPane Tabs (Right Pane 60%)
  - [ ] MetricsTab with KPI cards and Recharts LineChart
  - [ ] TokenHeatmapTab with score interpolation and animations
  - [ ] KVCacheTab visualizer

## Integration & Verification
- [ ] Run backend using micromamba `dl` env
- [ ] Connect frontend to WS endpoint and test end-to-end payload handling
- [ ] Verify animations, layout responsiveness, and dark mode aesthetic
- [ ] Fix any visual or functional bugs

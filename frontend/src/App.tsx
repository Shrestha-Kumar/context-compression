import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Settings from './pages/Settings';
import Terminal from './pages/Terminal';
import TemplatePage from './pages/TemplatePage';
import { TransitionOverlay } from './components/TransitionOverlay';
import { WebSocketProvider } from './hooks/useWebSocket';

export default function App() {
  return (
    <BrowserRouter>
      <WebSocketProvider url="ws://localhost:8000/ws" />
      <TransitionOverlay />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/terminal" element={<Terminal />} />
        <Route path="/telemetry" element={<TemplatePage title="Telemetry" context="Real-time ingestion" />} />
        <Route path="/compression" element={<TemplatePage title="Compression" context="Signal processing" />} />
        <Route path="/weights" element={<TemplatePage title="Weights" context="Neural network parameter" />} />
        <Route path="/latency" element={<TemplatePage title="Latency" context="Historical performance" />} />
        <Route path="/database" element={<TemplatePage title="Database" context="Vector embedding" />} />
      </Routes>
    </BrowserRouter>
  );
}

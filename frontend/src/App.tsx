import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import React from 'react';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Sessions from './pages/Sessions';
import Terminal from './pages/Terminal';
import Telemetry from './pages/Telemetry';
import Weights from './pages/Weights';
import Latency from './pages/Latency';
import Database from './pages/Database';
import { TransitionOverlay } from './components/TransitionOverlay';
import { WebSocketProvider } from './hooks/useWebSocket';

export default function App() {
  return (
    <BrowserRouter>
      <WebSocketProvider url="ws://localhost:8000/ws" />
      <TransitionOverlay />
      <Routes>
        <Route path="/" element={<Landing />} />
          {/* Both dashboard and compression will render the main Compression workspace */}
          <Route path="/dashboard" element={<Navigate to="/compression" replace />} />
          <Route path="/compression" element={<Dashboard />} />
          
          <Route path="/terminal" element={<Terminal />} />
          <Route path="/sessions" element={<Sessions />} />
          
          {/* Dynamic Functional Pages */}
          <Route path="/telemetry" element={<Telemetry />} />
          <Route path="/weights" element={<Weights />} />
          <Route path="/latency" element={<Latency />} />
          <Route path="/database" element={<Database />} />
        </Routes>
    </BrowserRouter>
  );
}

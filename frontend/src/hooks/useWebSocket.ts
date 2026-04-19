import { useEffect, useRef, useCallback } from 'react';
import { useAppStore } from '../store/appStore';

export function WebSocketProvider({ url }: { url: string }) {
  const ws = useRef<WebSocket | null>(null);
  const { appendMessage, setMessages, updateMetrics, setWsConnected, updateConstraints, updateTokenHeatmap, updateKVCache, _setSendMessage, currentSessionId, setCurrentSessionId } = useAppStore();

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    ws.current = new WebSocket(url);

    ws.current.onopen = () => {
      setWsConnected(true);
      // Re-identify whenever we connect
      if (currentSessionId) {
        ws.current?.send(JSON.stringify({ type: 'identify', session_id: currentSessionId }));
      }
    };

    // Reactive identity: if session ID changes while socket is open, tell the backend
    if (ws.current?.readyState === WebSocket.OPEN && currentSessionId) {
      ws.current.send(JSON.stringify({ type: 'identify', session_id: currentSessionId }));
    }

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'assistant_message':
            appendMessage({
              id: `#0${data.turn_number}`,
              tokens: `↓ ${data.output_tokens || 0} tok`,
              text: data.text,
              isUser: false
            });
            break;
            
          case 'compression_stats':
            updateMetrics({
              compRatio: data.ratio || 0,
              tokens: data.compressed_tokens || 0,
              vram_mb: data.vram_mb || 0,
              raw_tokens: data.raw_tokens || 0,
              compressed_tokens: data.compressed_tokens || 0,
              turn: `#0${data.turn_number || 0}`
            });
            break;
            
          case 'constraint_update':
            if (data.constraints) {
              updateConstraints(data.constraints);
            }
            break;

          case 'token_scores':
            if (data.tokens) {
              updateTokenHeatmap(data.tokens);
            }
            break;

          case 'kv_cache_state':
            updateKVCache({
              evicted_count: data.evicted_count,
              window_size: data.window_size
            });
            break;
            
          case 'session_update':
            if (data.session_id) {
              setCurrentSessionId(data.session_id);
            }
            break;

          case 'error':
            console.error("Backend Error:", data.message);
            break;
        }
      } catch (e) {
        console.error("Failed to parse WS message", e);
      }
    };

    ws.current.onclose = () => {
      setWsConnected(false);
      // Auto-reconnect after 3 seconds
      setTimeout(connect, 3000);
    };

  }, [url, appendMessage, updateMetrics, setWsConnected, currentSessionId]); // Added currentSessionId dependency

  useEffect(() => {
    connect();
    return () => {
      ws.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback((text: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ 
        type: 'user_message', 
        text,
        session_id: currentSessionId 
      }));
    }
  }, [currentSessionId]); // Fixed stale closure

  useEffect(() => {
    _setSendMessage(sendMessage);
  }, [sendMessage, _setSendMessage]);

  return null;
}

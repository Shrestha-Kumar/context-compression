import sqlite3
import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, messages_to_dict, messages_from_dict

logger = logging.getLogger("storage")

class StorageManager:
    def __init__(self, db_path: str = "backend/data/kinetic_sys.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    memory_state TEXT,
                    compression_history TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    turn_number INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    def get_sessions(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT id, name, created_at, updated_at FROM sessions ORDER BY updated_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            session = cursor.fetchone()
            if not session:
                return None
            
            # Load messages
            cursor = conn.execute("SELECT role, content, turn_number FROM messages WHERE session_id = ? ORDER BY id ASC", (session_id,))
            msg_dicts = [json.loads(row["content"]) for row in cursor.fetchall()]
            messages = messages_from_dict(msg_dicts)
            
            return {
                "id": session["id"],
                "name": session["name"],
                "memory": json.loads(session["memory_state"]),
                "compression_history": json.loads(session["compression_history"]),
                "messages": messages
            }

    def save_session(self, session_id: str, state: Dict[str, Any]):
        """Saves current state. If session exists, updates it; otherwise creates."""
        memory_json = json.dumps(state.get("memory", {}))
        comp_hist_json = json.dumps(state.get("compression_history", []))
        
        with sqlite3.connect(self.db_path) as conn:
            # Upsert session
            conn.execute("""
                INSERT INTO sessions (id, name, memory_state, compression_history, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    memory_state = excluded.memory_state,
                    compression_history = excluded.compression_history,
                    updated_at = excluded.updated_at
            """, (
                str(session_id), 
                str(state.get("name", f"Session {str(session_id)[:6]}")), 
                memory_json, 
                comp_hist_json,
                datetime.now().isoformat()
            ))
            
            # Sync messages (simplified: clear and re-insert for this turn or just append if logic allowed)
            # For simplicity in this stateful agent, we'll clear and re-insert the message list
            # which matches the LangGraph 'messages' list length.
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            
            msg_dicts = messages_to_dict(state.get("messages", []))
            for i, m_dict in enumerate(msg_dicts):
                conn.execute("""
                    INSERT INTO messages (session_id, role, content, turn_number)
                    VALUES (?, ?, ?, ?)
                """, (session_id, m_dict["type"], json.dumps(m_dict), i))
            
            conn.commit()

    def delete_session(self, session_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()

import os
storage = StorageManager()

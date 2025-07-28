"""
Memory Layer - Context persistence across interactions
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import os

class MemoryType(Enum):
    """Types of memory storage"""
    CONVERSATION = "conversation"
    PROJECT_STATE = "project_state"
    USER_PREFERENCES = "user_preferences"
    TEMPLATE_HISTORY = "template_history"
    FEEDBACK_HISTORY = "feedback_history"
    SYSTEM_STATE = "system_state"

@dataclass
class MemoryEntry:
    """Represents a memory entry"""
    id: str
    type: MemoryType
    key: str
    value: Any
    timestamp: datetime
    ttl: Optional[int] = None  # Time to live in seconds
    metadata: Optional[Dict[str, Any]] = None

class MemoryLayer:
    """Handles context persistence across interactions using in-memory storage"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.memory_store: Dict[str, MemoryEntry] = {}
    
    def store(self, memory_type: MemoryType, key: str, value: Any, ttl: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a value in memory"""
        entry_id = f"{memory_type.value}_{key}_{int(time.time())}"
        
        entry = MemoryEntry(
            id=entry_id,
            type=memory_type,
            key=key,
            value=value,
            timestamp=datetime.now(),
            ttl=ttl,
            metadata=metadata or {}
        )
        
        # Store in memory
        self.memory_store[entry_id] = entry
        
        self.logger.info(f"Stored memory entry: {entry_id}")
        return entry_id
    
    def retrieve(self, memory_type: MemoryType, key: str) -> Optional[Any]:
        """Retrieve a value from memory"""
        # Find the most recent entry for this type and key
        matching_entries = [
            entry for entry in self.memory_store.values()
            if entry.type == memory_type and entry.key == key
        ]
        
        if not matching_entries:
            return None
        
        # Return the most recent entry
        latest_entry = max(matching_entries, key=lambda x: x.timestamp)
        
        # Check if entry has expired
        if latest_entry.ttl:
            age = (datetime.now() - latest_entry.timestamp).total_seconds()
            if age > latest_entry.ttl:
                # Remove expired entry
                del self.memory_store[latest_entry.id]
                return None
        
        return latest_entry.value
    
    def retrieve_all(self, memory_type: MemoryType) -> List[MemoryEntry]:
        """Retrieve all entries of a specific type"""
        entries = [
            entry for entry in self.memory_store.values()
            if entry.type == memory_type
        ]
        
        # Filter out expired entries
        current_time = datetime.now()
        valid_entries = []
        expired_entries = []
        
        for entry in entries:
            if entry.ttl:
                age = (current_time - entry.timestamp).total_seconds()
                if age > entry.ttl:
                    expired_entries.append(entry.id)
                else:
                    valid_entries.append(entry)
            else:
                valid_entries.append(entry)
        
        # Remove expired entries
        for entry_id in expired_entries:
            del self.memory_store[entry_id]
        
        return valid_entries
    
    def delete(self, memory_type: MemoryType, key: str) -> bool:
        """Delete entries for a specific type and key"""
        entries_to_delete = [
            entry_id for entry_id, entry in self.memory_store.items()
            if entry.type == memory_type and entry.key == key
        ]
        
        for entry_id in entries_to_delete:
            del self.memory_store[entry_id]
        
        return len(entries_to_delete) > 0
    
    def clear_expired(self) -> int:
        """Clear all expired entries and return count of cleared entries"""
        current_time = datetime.now()
        expired_entries = []
        
        for entry_id, entry in self.memory_store.items():
            if entry.ttl:
                age = (current_time - entry.timestamp).total_seconds()
                if age > entry.ttl:
                    expired_entries.append(entry_id)
        
        for entry_id in expired_entries:
            del self.memory_store[entry_id]
        
        return len(expired_entries)
    
    def store_conversation_context(self, session_id: str, messages: List[Dict[str, str]], max_messages: int = 50) -> str:
        """Store conversation context for a session"""
        # Keep only the most recent messages
        if len(messages) > max_messages:
            messages = messages[-max_messages:]
        
        return self.store(
            MemoryType.CONVERSATION,
            session_id,
            messages,
            ttl=3600,  # 1 hour TTL
            metadata={"message_count": len(messages)}
        )
    
    def retrieve_conversation_context(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieve conversation context for a session"""
        context = self.retrieve(MemoryType.CONVERSATION, session_id)
        return context if context else []
    
    def store_project_state(self, project_id: str, state: Dict[str, Any]) -> str:
        """Store project state"""
        return self.store(
            MemoryType.PROJECT_STATE,
            project_id,
            state,
            ttl=7200,  # 2 hours TTL
            metadata={"last_updated": datetime.now().isoformat()}
        )
    
    def retrieve_project_state(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve project state"""
        return self.retrieve(MemoryType.PROJECT_STATE, project_id)
    
    def store_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> str:
        """Store user preferences"""
        return self.store(
            MemoryType.USER_PREFERENCES,
            user_id,
            preferences,
            ttl=86400,  # 24 hours TTL
            metadata={"last_updated": datetime.now().isoformat()}
        )
    
    def retrieve_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user preferences"""
        return self.retrieve(MemoryType.USER_PREFERENCES, user_id)
    
    def store_template_history(self, user_id: str, template_data: Dict[str, Any]) -> str:
        """Store template usage history"""
        return self.store(
            MemoryType.TEMPLATE_HISTORY,
            f"{user_id}_template_{int(time.time())}",
            template_data,
            ttl=604800,  # 7 days TTL
            metadata={"user_id": user_id, "timestamp": datetime.now().isoformat()}
        )
    
    def retrieve_template_history(self, user_id: str, limit: int = 10) -> List[MemoryEntry]:
        """Retrieve template history for a user"""
        all_entries = self.retrieve_all(MemoryType.TEMPLATE_HISTORY)
        user_entries = [
            entry for entry in all_entries
            if entry.metadata and entry.metadata.get("user_id") == user_id
        ]
        
        # Sort by timestamp and return most recent
        user_entries.sort(key=lambda x: x.timestamp, reverse=True)
        return user_entries[:limit]
    
    def create_session_context(self, session_id: str, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new session context"""
        session_context = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "conversation_count": 0,
            "project_state": {},
            "user_preferences": {},
            **initial_data
        }
        
        self.store(
            MemoryType.SYSTEM_STATE,
            session_id,
            session_context,
            ttl=3600,  # 1 hour TTL
            metadata={"type": "session_context"}
        )
        
        return session_context
    
    def update_session_context(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session context"""
        current_context = self.retrieve(MemoryType.SYSTEM_STATE, session_id)
        
        if not current_context:
            return False
        
        # Update the context
        current_context.update(updates)
        current_context["last_activity"] = datetime.now().isoformat()
        
        # Store the updated context
        self.store(
            MemoryType.SYSTEM_STATE,
            session_id,
            current_context,
            ttl=3600,  # 1 hour TTL
            metadata={"type": "session_context"}
        )
        
        return True
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        self.clear_expired()  # Clean up expired entries first
        
        stats = {
            "total_entries": len(self.memory_store),
            "entries_by_type": {},
            "memory_usage_mb": 0
        }
        
        # Count entries by type
        for entry in self.memory_store.values():
            entry_type = entry.type.value
            if entry_type not in stats["entries_by_type"]:
                stats["entries_by_type"][entry_type] = 0
            stats["entries_by_type"][entry_type] += 1
        
        # Estimate memory usage (rough calculation)
        try:
            import sys
            stats["memory_usage_mb"] = round(sys.getsizeof(self.memory_store) / (1024 * 1024), 2)
        except:
            stats["memory_usage_mb"] = 0
        
        return stats 
"""
Conversation repository for conversation data operations
"""
import logging
from typing import List, Dict, Any, Optional
from backend.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

class ConversationRepository(BaseRepository):
    """Repository for conversation operations"""

    def __init__(self):
        super().__init__('conversations')

    def get_conversations_with_message_count(self) -> List[Dict[str, Any]]:
        """Get all conversations with message counts"""
        try:
            query = """
                SELECT c.*, COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN chat_messages m ON c.id = m.conversation_id
                GROUP BY c.id
                ORDER BY c.updated_at DESC
            """
            return self.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting conversations with message count: {e}")
            return []

    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations"""
        try:
            query = """
                SELECT c.*, COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN chat_messages m ON c.id = m.conversation_id
                GROUP BY c.id
                ORDER BY c.updated_at DESC
                LIMIT ?
            """
            return self.execute_query(query, (limit,))
        except Exception as e:
            logger.error(f"Error getting recent conversations: {e}")
            return []

    def update_title(self, conversation_id: int, title: str) -> bool:
        """Update conversation title"""
        try:
            data = {'title': title}
            return self.update(conversation_id, data)
        except Exception as e:
            logger.error(f"Error updating conversation title: {e}")
            return False

    def get_messages(self, conversation_id: int) -> List[Dict[str, Any]]:
        """Get all messages for a conversation"""
        try:
            query = """
                SELECT * FROM chat_messages
                WHERE conversation_id = ?
                ORDER BY created_at ASC
            """
            return self.execute_query(query, (conversation_id,))
        except Exception as e:
            logger.error(f"Error getting conversation messages: {e}")
            return []

    def add_message(self, conversation_id: int, role: str, message: str) -> Optional[int]:
        """Add a message to conversation and update conversation's updated_at timestamp"""
        try:
            # Add the message
            query = """
                INSERT INTO chat_messages (conversation_id, role, message)
                VALUES (?, ?, ?)
            """
            message_id = self.execute_insert(query, (conversation_id, role, message))
            
            # Update conversation's updated_at timestamp
            if message_id:
                update_query = """
                    UPDATE conversations 
                    SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """
                self.execute_update(update_query, (conversation_id,))
            
            return message_id
        except Exception as e:
            logger.error(f"Error adding message to conversation: {e}")
            return None

    def delete_messages(self, conversation_id: int) -> bool:
        """Delete all messages for a conversation"""
        try:
            query = "DELETE FROM chat_messages WHERE conversation_id = ?"
            return self.execute_update(query, (conversation_id,)) >= 0
        except Exception as e:
            logger.error(f"Error deleting conversation messages: {e}")
            return False

    def to_dict(self, record: Any) -> Dict[str, Any]:
        """Convert conversation record to dictionary"""
        if isinstance(record, dict):
            return record
        return dict(record) if hasattr(record, 'keys') else {}

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute custom query (helper method)"""
        from backend.models.database import execute_query
        return execute_query(query, params)

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute update query (helper method)"""
        from backend.models.database import execute_update
        return execute_update(query, params)

    def execute_insert(self, query: str, params: tuple = ()) -> Optional[int]:
        """Execute insert query (helper method)"""
        from backend.models.database import execute_insert
        return execute_insert(query, params)

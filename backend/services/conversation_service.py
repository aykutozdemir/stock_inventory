"""
Conversation service for conversation business logic
"""
import logging
from typing import List, Dict, Any, Optional
from backend.repositories.conversation_repository import ConversationRepository
from backend.utils.validation import validate_conversation_data, validate_message_data, ValidationError

logger = logging.getLogger(__name__)

class ConversationService:
    """Service for conversation operations"""

    def __init__(self):
        self.repository = ConversationRepository()

    def get_all_conversations(self) -> List[Dict[str, Any]]:
        """Get all conversations with message counts"""
        try:
            return self.repository.get_conversations_with_message_count()
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            return []

    def get_conversation(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """Get conversation by ID"""
        try:
            conversation = self.repository.find_by_id(conversation_id)
            if conversation:
                messages = self.repository.get_messages(conversation_id)
                conversation['messages'] = messages
            return conversation
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {e}")
            return None

    def create_conversation(self, title: str = None) -> Dict[str, Any]:
        """Create new conversation"""
        try:
            if not title:
                title = "New Conversation"

            data = {'title': title}
            validated_data = validate_conversation_data(data)

            conversation_id = self.repository.create(validated_data)
            if conversation_id:
                conversation = self.repository.find_by_id(conversation_id)
                return {
                    'success': True,
                    'message': 'Conversation created successfully',
                    'data': {'id': conversation_id, **conversation} if conversation else None
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to create conversation',
                    'data': None
                }

        except ValidationError as e:
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return {
                'success': False,
                'message': 'Internal server error',
                'data': None
            }

    def update_conversation_title(self, conversation_id: int, title: str) -> Dict[str, Any]:
        """Update conversation title"""
        try:
            validated_data = validate_conversation_data({'title': title})

            success = self.repository.update_title(conversation_id, validated_data['title'])
            if success:
                return {
                    'success': True,
                    'message': 'Title updated successfully',
                    'data': None
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to update title',
                    'data': None
                }

        except ValidationError as e:
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
        except Exception as e:
            logger.error(f"Error updating conversation title: {e}")
            return {
                'success': False,
                'message': 'Internal server error',
                'data': None
            }

    def delete_conversation(self, conversation_id: int) -> Dict[str, Any]:
        """Delete conversation"""
        try:
            success = self.repository.delete(conversation_id)
            if success:
                return {
                    'success': True,
                    'message': 'Conversation deleted successfully',
                    'data': None
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to delete conversation',
                    'data': None
                }

        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return {
                'success': False,
                'message': 'Internal server error',
                'data': None
            }

    def get_messages(self, conversation_id: int) -> List[Dict[str, Any]]:
        """Get all messages for a conversation"""
        try:
            return self.repository.get_messages(conversation_id)
        except Exception as e:
            logger.error(f"Error getting messages for conversation {conversation_id}: {e}")
            return []

    def add_message(self, conversation_id: int, role: str, message: str) -> Dict[str, Any]:
        """Add message to conversation"""
        try:
            validated_data = validate_message_data({'role': role, 'message': message})

            message_id = self.repository.add_message(
                conversation_id,
                validated_data['role'],
                validated_data['message']
            )

            if message_id:
                return {
                    'success': True,
                    'message': 'Message added successfully',
                    'data': {'id': message_id}
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to add message',
                    'data': None
                }

        except ValidationError as e:
            return {
                'success': False,
                'message': str(e),
                'data': None
            }
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return {
                'success': False,
                'message': 'Internal server error',
                'data': None
            }

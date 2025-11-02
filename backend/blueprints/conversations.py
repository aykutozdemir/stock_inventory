"""
Conversations blueprint
Handles conversation-related API endpoints.
"""
import logging
import time
from flask import Blueprint, request, jsonify
from backend.services.conversation_service import ConversationService
from backend.utils.security import sanitize_input
from backend.utils.logger import get_request_logger, log_request

logger = get_request_logger()
conversations_bp = Blueprint('conversations', __name__, url_prefix='/api/conversations')
conversation_service = ConversationService()

@conversations_bp.route('', methods=['GET'])
def get_conversations():
    """Get all conversations"""
    start_time = time.time()

    try:
        conversations = conversation_service.get_all_conversations()

        response = jsonify({
            'success': True,
            'message': f'Conversations retrieved successfully ({len(conversations)} conversations)',
            'data': conversations
        })

        log_request(logger, 'GET', request.path, 200, time.time() - start_time)
        return response

    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        log_request(logger, 'GET', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@conversations_bp.route('/<int:conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get conversation by ID with messages"""
    start_time = time.time()

    try:
        conversation = conversation_service.get_conversation(conversation_id)

        if conversation:
            response = jsonify({
                'success': True,
                'message': 'Conversation retrieved successfully',
                'data': conversation
            })
            log_request(logger, 'GET', request.path, 200, time.time() - start_time)
            return response
        else:
            response = jsonify({
                'success': False,
                'message': 'Conversation not found',
                'data': None
            }), 404
            log_request(logger, 'GET', request.path, 404, time.time() - start_time)
            return response

    except Exception as e:
        logger.error(f"Error getting conversation {conversation_id}: {e}")
        log_request(logger, 'GET', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@conversations_bp.route('', methods=['POST'])
def create_conversation():
    """Create new conversation"""
    start_time = time.time()

    try:
        data = request.get_json()

        title = data.get('title', '').strip() if data else ''
        if not title:
            title = f"Conversation {int(time.time())}"

        # Sanitize title
        title = sanitize_input(title)

        result = conversation_service.create_conversation(title)

        status_code = 201 if result['success'] else 400
        response = jsonify(result)
        log_request(logger, 'POST', request.path, status_code, time.time() - start_time)
        return response, status_code

    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        log_request(logger, 'POST', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@conversations_bp.route('/<int:conversation_id>/title', methods=['PUT'])
def update_conversation_title(conversation_id):
    """Update conversation title"""
    start_time = time.time()

    try:
        data = request.get_json()

        if not data or 'title' not in data:
            response = jsonify({
                'success': False,
                'message': 'Title is required',
                'data': None
            }), 400
            log_request(logger, 'PUT', request.path, 400, time.time() - start_time)
            return response

        title = sanitize_input(data['title'])

        result = conversation_service.update_conversation_title(conversation_id, title)

        status_code = 200 if result['success'] else 400
        response = jsonify(result)
        log_request(logger, 'PUT', request.path, status_code, time.time() - start_time)
        return response, status_code

    except Exception as e:
        logger.error(f"Error updating conversation title: {e}")
        log_request(logger, 'PUT', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@conversations_bp.route('/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete conversation"""
    start_time = time.time()

    try:
        result = conversation_service.delete_conversation(conversation_id)

        status_code = 200 if result['success'] else 400
        response = jsonify(result)
        log_request(logger, 'DELETE', request.path, status_code, time.time() - start_time)
        return response, status_code

    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        log_request(logger, 'DELETE', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@conversations_bp.route('/<int:conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    """Get all messages for a conversation"""
    start_time = time.time()

    try:
        messages = conversation_service.get_messages(conversation_id)

        response = jsonify({
            'success': True,
            'message': f'Messages retrieved successfully ({len(messages)} messages)',
            'data': messages
        })

        log_request(logger, 'GET', request.path, 200, time.time() - start_time)
        return response

    except Exception as e:
        logger.error(f"Error getting conversation messages: {e}")
        log_request(logger, 'GET', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@conversations_bp.route('/<int:conversation_id>/messages', methods=['POST'])
def add_message_to_conversation(conversation_id):
    """Add a message to a conversation"""
    start_time = time.time()

    try:
        data = request.get_json()

        if not data:
            response = jsonify({
                'success': False,
                'message': 'No data provided',
                'data': None
            }), 400
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return response

        role = data.get('role', '').strip()
        message = data.get('message', '').strip()

        if not role or not message:
            response = jsonify({
                'success': False,
                'message': 'Role and message are required',
                'data': None
            }), 400
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return response

        if role not in ['user', 'assistant']:
            response = jsonify({
                'success': False,
                'message': 'Role must be either "user" or "assistant"',
                'data': None
            }), 400
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return response

        # Sanitize message
        message = sanitize_input(message)

        result = conversation_service.add_message(conversation_id, role, message)

        status_code = 201 if result['success'] else 400
        response = jsonify(result)
        log_request(logger, 'POST', request.path, status_code, time.time() - start_time)
        return response, status_code

    except Exception as e:
        logger.error(f"Error adding message to conversation: {e}")
        log_request(logger, 'POST', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

"""
AI blueprint
Handles AI assistant and conversation-related API endpoints.
"""
import logging
import time
import json
import queue
import threading
from flask import Blueprint, request, jsonify, Response, stream_with_context
from backend.services.ai_service import AIService
from backend.services.conversation_service import ConversationService
from backend.utils.security import sanitize_input, rate_limit_check
from backend.utils.logger import get_request_logger, log_request

logger = get_request_logger()
ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')
ai_service = AIService()
conversation_service = ConversationService()

@ai_bp.route('/ask', methods=['POST'])
def ai_ask():
    """AI assistant question answering"""
    start_time = time.time()

    try:
        # Rate limiting check
        client_ip = request.remote_addr or 'unknown'
        if not rate_limit_check(client_ip, max_requests=50, window_seconds=60):
            response = jsonify({
                'success': False,
                'message': 'Rate limit exceeded. Please wait before making another request.',
                'data': None
            }), 429
            log_request(logger, 'POST', request.path, 429, time.time() - start_time)
            return response

        data = request.get_json()

        if not data:
            response = jsonify({
                'success': False,
                'message': 'No data provided',
                'data': None
            }), 400
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return response

        user_question = data.get('question', '').strip()
        conversation_id = data.get('conversation_id')

        if not user_question:
            response = jsonify({
                'success': False,
                'message': 'Question is required',
                'data': None
            }), 400
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return response

        # Sanitize input
        user_question = sanitize_input(user_question)

        # Persist user message if conversation_id is provided
        try:
            if conversation_id:
                conversation_service.add_message(conversation_id, 'user', user_question)
        except Exception as e:
            logger.error(f"Failed to store user message: {e}")

        # Process AI request
        result = ai_service.process_question(user_question, conversation_id)

        # Persist assistant response if conversation_id is provided
        try:
            if conversation_id:
                if result.get('success') and result.get('data'):
                    assistant_text = result['data'].get('answer', '') or ''
                else:
                    assistant_text = result.get('message', '') or ''
                if assistant_text:
                    conversation_service.add_message(conversation_id, 'assistant', assistant_text)
        except Exception as e:
            logger.error(f"Failed to store assistant message: {e}")

        status_code = 200 if result['success'] else 400
        response = jsonify(result)
        log_request(logger, 'POST', request.path, status_code, time.time() - start_time)
        return response, status_code

    except Exception as e:
        logger.error(f"Error processing AI request: {e}")
        log_request(logger, 'POST', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@ai_bp.route('/calculate', methods=['POST'])
def electronics_calculate():
    """Electronics calculations"""
    start_time = time.time()

    try:
        # Rate limiting check
        client_ip = request.remote_addr or 'unknown'
        if not rate_limit_check(client_ip, max_requests=100, window_seconds=60):
            response = jsonify({
                'success': False,
                'message': 'Rate limit exceeded. Please wait before making another request.',
                'data': None
            }), 429
            log_request(logger, 'POST', request.path, 429, time.time() - start_time)
            return response

        data = request.get_json()

        if not data:
            response = jsonify({
                'success': False,
                'message': 'No data provided',
                'data': None
            }), 400
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return response

        calculation_type = data.get('type', '').strip()
        params = data.get('params', {})

        if not calculation_type:
            response = jsonify({
                'success': False,
                'message': 'Calculation type is required',
                'data': None
            }), 400
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return response

        # Sanitize input
        calculation_type = sanitize_input(calculation_type)

        result = ai_service.perform_calculation(calculation_type, params)

        status_code = 200 if result['success'] else 400
        response = jsonify(result)
        log_request(logger, 'POST', request.path, status_code, time.time() - start_time)
        return response, status_code

    except Exception as e:
        logger.error(f"Error performing calculation: {e}")
        log_request(logger, 'POST', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@ai_bp.route('/search', methods=['POST'])
def component_search():
    """Search for electronic component specifications"""
    start_time = time.time()

    try:
        # Rate limiting check
        client_ip = request.remote_addr or 'unknown'
        if not rate_limit_check(client_ip, max_requests=30, window_seconds=60):
            response = jsonify({
                'success': False,
                'message': 'Rate limit exceeded. Please wait before making another request.',
                'data': None
            }), 429
            log_request(logger, 'POST', request.path, 429, time.time() - start_time)
            return response

        data = request.get_json()

        if not data:
            response = jsonify({
                'success': False,
                'message': 'No data provided',
                'data': None
            }), 400
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return response

        query = data.get('query', '').strip()

        if not query:
            response = jsonify({
                'success': False,
                'message': 'Search query is required',
                'data': None
            }), 400
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return response

        # Sanitize input
        query = sanitize_input(query)

        result = ai_service.search_component(query)

        status_code = 200 if result['success'] else 400
        response = jsonify(result)
        log_request(logger, 'POST', request.path, status_code, time.time() - start_time)
        return response, status_code

    except Exception as e:
        logger.error(f"Error searching component: {e}")
        log_request(logger, 'POST', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@ai_bp.route('/generate-summary', methods=['POST'])
def generate_datasheet_summary():
    """Generate comprehensive summary from datasheet PDF"""
    start_time = time.time()

    try:
        # Rate limiting check
        client_ip = request.remote_addr or 'unknown'
        if not rate_limit_check(client_ip, max_requests=20, window_seconds=60):
            response = jsonify({
                'success': False,
                'message': 'Rate limit exceeded. Please wait before making another request.',
                'data': None
            }), 429
            log_request(logger, 'POST', request.path, 429, time.time() - start_time)
            return response

        # Check if PDF file was uploaded
        if 'pdf_file' not in request.files:
            response = jsonify({
                'success': False,
                'message': 'PDF file is required',
                'data': None
            }), 400
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return response

        pdf_file = request.files['pdf_file']
        component_name = request.form.get('component_name', '').strip()

        if not pdf_file or pdf_file.filename == '':
            response = jsonify({
                'success': False,
                'message': 'Valid PDF file is required',
                'data': None
            }), 400
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return response

        # Validate file type
        if not pdf_file.filename.lower().endswith('.pdf'):
            response = jsonify({
                'success': False,
                'message': 'Only PDF files are supported',
                'data': None
            }), 400
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return response

        # Read PDF data
        pdf_data = pdf_file.read()

        # Sanitize component name
        component_name = sanitize_input(component_name) if component_name else ""

        # Generate summary
        result = ai_service.generate_datasheet_summary(pdf_data, component_name)

        status_code = 200 if result['success'] else 400
        response = jsonify(result)
        log_request(logger, 'POST', request.path, status_code, time.time() - start_time)
        return response, status_code

    except Exception as e:
        logger.error(f"Error generating datasheet summary: {e}")
        log_request(logger, 'POST', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@ai_bp.route('/ask/stream', methods=['POST'])
def ai_ask_stream():
    """AI assistant question answering with Server-Sent Events progress streaming"""
    start_time = time.time()

    try:
        # Rate limiting check
        client_ip = request.remote_addr or 'unknown'
        if not rate_limit_check(client_ip, max_requests=50, window_seconds=60):
            log_request(logger, 'POST', request.path, 429, time.time() - start_time)
            return Response(
                f"event: error\ndata: {json.dumps({'message': 'Rate limit exceeded'})}\n\n",
                mimetype='text/event-stream'
            ), 429

        data = request.get_json()

        if not data:
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return Response(
                f"event: error\ndata: {json.dumps({'message': 'No data provided'})}\n\n",
                mimetype='text/event-stream'
            ), 400

        user_question = data.get('question', '').strip()
        conversation_id = data.get('conversation_id')

        if not user_question:
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return Response(
                f"event: error\ndata: {json.dumps({'message': 'Question is required'})}\n\n",
                mimetype='text/event-stream'
            ), 400

        # Sanitize input
        user_question = sanitize_input(user_question)

        # Persist user message if conversation_id is provided
        try:
            if conversation_id:
                conversation_service.add_message(conversation_id, 'user', user_question)
        except Exception as e:
            logger.error(f"Failed to store user message: {e}")

        def generate():
            """Generator function to stream SSE events"""
            result_data = None
            progress_queue = queue.Queue()
            processing_done = threading.Event()
            error_occurred = threading.Event()
            
            def progress_callback(message):
                """Callback to send progress updates"""
                try:
                    progress_queue.put(('progress', message))
                except:
                    pass
            
            def process_ai_request():
                """Process AI request in separate thread"""
                nonlocal result_data
                try:
                    result_data = ai_service.process_question(user_question, conversation_id, progress_callback)
                    
                    # Persist assistant response if conversation_id is provided
                    try:
                        if conversation_id:
                            if result_data.get('success') and result_data.get('data'):
                                assistant_text = result_data['data'].get('answer', '') or ''
                            else:
                                assistant_text = result_data.get('message', '') or ''
                            if assistant_text:
                                conversation_service.add_message(conversation_id, 'assistant', assistant_text)
                    except Exception as e:
                        logger.error(f"Failed to store assistant message: {e}")
                    
                    processing_done.set()
                except Exception as e:
                    logger.error(f"Error in streaming AI request: {e}")
                    error_occurred.set()
            
            # Start processing in background thread
            thread = threading.Thread(target=process_ai_request)
            thread.daemon = True
            thread.start()
            
            try:
                # Stream progress updates while processing
                while not processing_done.is_set() and not error_occurred.is_set():
                    try:
                        event_type, data = progress_queue.get(timeout=0.1)
                        yield f"event: progress\ndata: {json.dumps({'message': data})}\n\n"
                    except queue.Empty:
                        continue
                    except Exception as e:
                        logger.error(f"Error streaming progress: {e}")
                
                # Wait for thread to complete
                thread.join(timeout=60)
                
                # Flush any remaining progress messages
                while not progress_queue.empty():
                    try:
                        event_type, data = progress_queue.get_nowait()
                        yield f"event: progress\ndata: {json.dumps({'message': data})}\n\n"
                    except queue.Empty:
                        break
                    except Exception as e:
                        logger.error(f"Error flushing progress: {e}")
                
                if error_occurred.is_set():
                    error_result = {
                        'success': False,
                        'message': 'Internal server error',
                        'data': None
                    }
                    yield f"event: error\ndata: {json.dumps(error_result)}\n\n"
                elif result_data:
                    # Send final result
                    yield f"event: result\ndata: {json.dumps(result_data)}\n\n"
                else:
                    error_result = {
                        'success': False,
                        'message': 'Request timed out',
                        'data': None
                    }
                    yield f"event: error\ndata: {json.dumps(error_result)}\n\n"
                
            except Exception as e:
                logger.error(f"Error in generator: {e}")
                error_result = {
                    'success': False,
                    'message': 'Internal server error',
                    'data': None
                }
                yield f"event: error\ndata: {json.dumps(error_result)}\n\n"

        response = Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
        log_request(logger, 'POST', request.path, 200, time.time() - start_time)
        return response

    except Exception as e:
        logger.error(f"Error processing streaming AI request: {e}")
        log_request(logger, 'POST', request.path, 500, time.time() - start_time)
        return Response(
            f"event: error\ndata: {json.dumps({'message': 'Internal server error'})}\n\n",
            mimetype='text/event-stream'
        ), 500

# Placeholder blueprints for conversations and datasheets
from flask import Blueprint

conversations_bp = Blueprint('conversations', __name__, url_prefix='/api/conversations')
datasheets_bp = Blueprint('datasheets', __name__, url_prefix='/api/datasheets')

@conversations_bp.route('', methods=['GET'])
def get_conversations():
    """Get all conversations"""
    return jsonify({'message': 'Conversations endpoint - TODO'})

@datasheets_bp.route('/<int:datasheet_id>')
def serve_datasheet(datasheet_id):
    """Serve PDF datasheet"""
    return jsonify({'message': 'Datasheets endpoint - TODO'})

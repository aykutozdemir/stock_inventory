"""
Datasheets blueprint
Handles datasheet-related API endpoints.
"""
import logging
import time
from flask import Blueprint, Response, request, jsonify
from backend.services.datasheet_service import DatasheetService
from backend.services.web_scraping_service import WebScrapingService
from backend.utils.security import sanitize_input, rate_limit_check
from backend.utils.logger import get_request_logger, log_request

logger = get_request_logger()
datasheets_bp = Blueprint('datasheets', __name__, url_prefix='/api/datasheets')
datasheet_service = DatasheetService()
web_scraping_service = WebScrapingService()

@datasheets_bp.route('/<int:datasheet_id>', methods=['GET'])
def serve_datasheet(datasheet_id):
    """Serve a PDF datasheet from database."""
    start_time = time.time()

    try:
        # Get PDF data
        pdf_data = datasheet_service.get_datasheet(datasheet_id)

        if pdf_data:
            # Get datasheet info for filename
            info = datasheet_service.get_datasheet_info(datasheet_id)
            filename = info['original_filename'] if info else f'datasheet_{datasheet_id}.pdf'

            response = Response(
                pdf_data,
                mimetype='application/pdf',
                headers={
                    'Content-Disposition': f'inline; filename="{filename}"',
                    'Content-Length': str(len(pdf_data))
                }
            )

            log_request(logger, 'GET', request.path, 200, time.time() - start_time)
            return response
        else:
            response = Response("Datasheet not found", status=404)
            log_request(logger, 'GET', request.path, 404, time.time() - start_time)
            return response

    except Exception as e:
        logger.error(f"Error serving datasheet {datasheet_id}: {e}")
        log_request(logger, 'GET', request.path, 500, time.time() - start_time)
        return Response("Error serving datasheet", status=500)

@datasheets_bp.route('/<int:datasheet_id>/summary', methods=['GET'])
def get_datasheet_summary(datasheet_id):
    """Get datasheet summary"""
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
            log_request(logger, 'GET', request.path, 429, time.time() - start_time)
            return response

        info = datasheet_service.get_datasheet_info(datasheet_id)
        if not info:
            response = jsonify({
                'success': False,
                'message': 'Datasheet not found',
                'data': None
            }), 404
            log_request(logger, 'GET', request.path, 404, time.time() - start_time)
            return response

        response = jsonify({
            'success': True,
            'message': 'Summary retrieved successfully',
            'data': {
                'datasheet_id': datasheet_id,
                'component_name': info['component_name'],
                'summary': info.get('summary', ''),
                'has_summary': bool(info.get('summary'))
            }
        })
        log_request(logger, 'GET', request.path, 200, time.time() - start_time)
        return response

    except Exception as e:
        logger.error(f"Error getting datasheet summary {datasheet_id}: {e}")
        log_request(logger, 'GET', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Error retrieving summary',
            'data': None
        }), 500

@datasheets_bp.route('/<int:datasheet_id>/summary', methods=['PUT'])
def update_datasheet_summary(datasheet_id):
    """Update datasheet summary"""
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
            log_request(logger, 'PUT', request.path, 429, time.time() - start_time)
            return response

        data = request.get_json()

        if not data:
            response = jsonify({
                'success': False,
                'message': 'No data provided',
                'data': None
            }), 400
            log_request(logger, 'PUT', request.path, 400, time.time() - start_time)
            return response

        summary = data.get('summary', '').strip()

        if not summary:
            response = jsonify({
                'success': False,
                'message': 'Summary text is required',
                'data': None
            }), 400
            log_request(logger, 'PUT', request.path, 400, time.time() - start_time)
            return response

        # Sanitize input
        summary = sanitize_input(summary)

        # Update summary
        success = datasheet_service.update_summary(datasheet_id, summary)

        if success:
            response = jsonify({
                'success': True,
                'message': 'Summary updated successfully',
                'data': {
                    'datasheet_id': datasheet_id,
                    'summary': summary
                }
            })
            log_request(logger, 'PUT', request.path, 200, time.time() - start_time)
            return response
        else:
            response = jsonify({
                'success': False,
                'message': 'Failed to update summary',
                'data': None
            }), 500
            log_request(logger, 'PUT', request.path, 500, time.time() - start_time)
            return response

    except Exception as e:
        logger.error(f"Error updating datasheet summary {datasheet_id}: {e}")
        log_request(logger, 'PUT', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Error updating summary',
            'data': None
        }), 500

@datasheets_bp.route('/<int:datasheet_id>/generate-summary', methods=['POST'])
def generate_datasheet_summary(datasheet_id):
    """Generate summary from existing datasheet PDF"""
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

        # Get datasheet info
        info = datasheet_service.get_datasheet_info(datasheet_id)
        if not info:
            response = jsonify({
                'success': False,
                'message': 'Datasheet not found',
                'data': None
            }), 404
            log_request(logger, 'POST', request.path, 404, time.time() - start_time)
            return response

        # Get PDF data
        pdf_data = datasheet_service.get_datasheet(datasheet_id)
        if not pdf_data:
            response = jsonify({
                'success': False,
                'message': 'PDF data not found',
                'data': None
            }), 404
            log_request(logger, 'POST', request.path, 404, time.time() - start_time)
            return response

        # Generate summary
        summary = web_scraping_service.generate_datasheet_summary(pdf_data, info['component_name'])

        if summary:
            # Update the datasheet with the generated summary
            success = datasheet_service.update_summary(datasheet_id, summary)

            if success:
                response = jsonify({
                    'success': True,
                    'message': 'Summary generated and saved successfully',
                    'data': {
                        'datasheet_id': datasheet_id,
                        'component_name': info['component_name'],
                        'summary': summary
                    }
                })
                log_request(logger, 'POST', request.path, 200, time.time() - start_time)
                return response
            else:
                response = jsonify({
                    'success': False,
                    'message': 'Summary generated but failed to save',
                    'data': {'summary': summary}
                }), 500
                log_request(logger, 'POST', request.path, 500, time.time() - start_time)
                return response
        else:
            response = jsonify({
                'success': False,
                'message': 'Failed to generate summary from PDF',
                'data': None
            }), 400
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return response

    except Exception as e:
        logger.error(f"Error generating datasheet summary {datasheet_id}: {e}")
        log_request(logger, 'POST', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Error generating summary',
            'data': None
        }), 500

@datasheets_bp.route('/search-summary', methods=['GET'])
def search_datasheets_by_summary():
    """Search datasheets by summary content"""
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
            log_request(logger, 'GET', request.path, 429, time.time() - start_time)
            return response

        query = request.args.get('q', '').strip()
        limit = request.args.get('limit', 10, type=int)

        if not query:
            response = jsonify({
                'success': False,
                'message': 'Search query is required',
                'data': None
            }), 400
            log_request(logger, 'GET', request.path, 400, time.time() - start_time)
            return response

        # Sanitize input
        query = sanitize_input(query)

        # Validate limit
        limit = min(max(limit, 1), 50)  # Between 1 and 50

        results = datasheet_service.search_by_summary(query, limit)

        response = jsonify({
            'success': True,
            'message': f'Found {len(results)} datasheets matching summary search',
            'data': {
                'query': query,
                'results': results,
                'count': len(results)
            }
        })
        log_request(logger, 'GET', request.path, 200, time.time() - start_time)
        return response

    except Exception as e:
        logger.error(f"Error searching datasheets by summary: {e}")
        log_request(logger, 'GET', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Error searching summaries',
            'data': None
        }), 500

@datasheets_bp.route('/with-summaries', methods=['GET'])
def get_datasheets_with_summaries():
    """Get datasheets that have summaries"""
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
            log_request(logger, 'GET', request.path, 429, time.time() - start_time)
            return response

        limit = request.args.get('limit', 50, type=int)
        limit = min(max(limit, 1), 100)  # Between 1 and 100

        results = datasheet_service.get_datasheets_with_summaries(limit)

        response = jsonify({
            'success': True,
            'message': f'Found {len(results)} datasheets with summaries',
            'data': {
                'results': results,
                'count': len(results)
            }
        })
        log_request(logger, 'GET', request.path, 200, time.time() - start_time)
        return response

    except Exception as e:
        logger.error(f"Error getting datasheets with summaries: {e}")
        log_request(logger, 'GET', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Error retrieving datasheets with summaries',
            'data': None
        }), 500

@datasheets_bp.route('/compare', methods=['POST'])
def compare_components():
    """Compare components based on specifications"""
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

        data = request.get_json()

        if not data:
            response = jsonify({
                'success': False,
                'message': 'No data provided',
                'data': None
            }), 400
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return response

        component_names = data.get('components', [])
        criteria = data.get('criteria', {})

        if not component_names or len(component_names) < 2:
            response = jsonify({
                'success': False,
                'message': 'Please provide at least 2 component names to compare',
                'data': None
            }), 400
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return response

        # Get comparison data
        comparison_data = datasheet_service.find_similar_components(
            voltage_min=criteria.get('voltage_min'),
            voltage_max=criteria.get('voltage_max'),
            current_min=criteria.get('current_min'),
            current_max=criteria.get('current_max'),
            power_min=criteria.get('power_min'),
            power_max=criteria.get('power_max'),
            component_type=criteria.get('component_type'),
            limit=20
        )

        # Filter by requested component names
        filtered_comparison = []
        for comp in comparison_data:
            comp_name_lower = comp['component_name'].lower()
            if any(req_name.lower() in comp_name_lower or comp_name_lower in req_name.lower() for req_name in component_names):
                filtered_comparison.append(comp)

        response = jsonify({
            'success': True,
            'message': f'Found {len(filtered_comparison)} components matching your criteria',
            'data': {
                'components': filtered_comparison,
                'criteria': criteria,
                'comparison_fields': [
                    'component_name', 'manufacturer', 'voltage_rating',
                    'current_rating', 'power_rating', 'temperature_range',
                    'tolerance', 'package_type'
                ]
            }
        })
        log_request(logger, 'POST', request.path, 200, time.time() - start_time)
        return response

    except Exception as e:
        logger.error(f"Error comparing components: {e}")
        log_request(logger, 'POST', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Error comparing components',
            'data': None
        }), 500

@datasheets_bp.route('/download/<component_name>', methods=['POST'])
def download_component_datasheet(component_name):
    """Download and save datasheet for a specific component"""
    start_time = time.time()

    try:
        # Rate limiting check
        client_ip = request.remote_addr or 'unknown'
        if not rate_limit_check(client_ip, max_requests=10, window_seconds=60):
            response = jsonify({
                'success': False,
                'message': 'Rate limit exceeded. Please wait before making another request.',
                'data': None
            }), 429
            log_request(logger, 'POST', request.path, 429, time.time() - start_time)
            return response

        # Import here to avoid circular imports
        from backend.services.web_scraping_service import WebScrapingService
        from backend.services.datasheet_service import DatasheetService

        web_scraping = WebScrapingService()
        datasheet_svc = DatasheetService()

        logger.info(f"Attempting to download datasheet for: {component_name}")

        # Try to download PDF
        pdf_data = web_scraping.download_datasheet_pdf(component_name)

        if pdf_data:
            # Save to database
            datasheet_id = datasheet_svc.save_datasheet(
                component_name=component_name,
                pdf_data=pdf_data['pdf_data'],
                source_url=pdf_data['source_url'],
                filename=pdf_data['filename'],
                extracted_specs=pdf_data.get('extracted_specs'),
                key_specifications=pdf_data.get('key_specifications'),
                manufacturer=pdf_data.get('manufacturer'),
                package_type=pdf_data.get('package_type'),
                voltage_rating=pdf_data.get('voltage_rating'),
                current_rating=pdf_data.get('current_rating'),
                power_rating=pdf_data.get('power_rating'),
                temperature_range=pdf_data.get('temperature_range'),
                tolerance=pdf_data.get('tolerance')
            )

            if datasheet_id:
                response = jsonify({
                    'success': True,
                    'message': f'Successfully downloaded and saved datasheet for {component_name}',
                    'data': {
                        'datasheet_id': datasheet_id,
                        'component_name': component_name,
                        'filename': pdf_data['filename'],
                        'source_url': pdf_data['source_url'],
                        'extracted_specs': pdf_data.get('extracted_specs'),
                        'specifications': {
                            'manufacturer': pdf_data.get('manufacturer'),
                            'package_type': pdf_data.get('package_type'),
                            'voltage_rating': pdf_data.get('voltage_rating'),
                            'current_rating': pdf_data.get('current_rating'),
                            'power_rating': pdf_data.get('power_rating'),
                            'temperature_range': pdf_data.get('temperature_range'),
                            'tolerance': pdf_data.get('tolerance')
                        }
                    }
                })
                log_request(logger, 'POST', request.path, 200, time.time() - start_time)
                return response
            else:
                response = jsonify({
                    'success': False,
                    'message': 'PDF downloaded but failed to save to database',
                    'data': None
                }), 500
                log_request(logger, 'POST', request.path, 500, time.time() - start_time)
                return response
        else:
            # Fallback: just provide search links
            search_results = web_scraping.search_component_specs(component_name)
            response = jsonify({
                'success': False,
                'message': f'Could not download PDF directly, but here are search results for {component_name}',
                'data': {
                    'search_results': search_results,
                    'component_name': component_name
                }
            }), 404
            log_request(logger, 'POST', request.path, 404, time.time() - start_time)
            return response

    except Exception as e:
        logger.error(f"Error downloading datasheet for {component_name}: {e}")
        log_request(logger, 'POST', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': f'Error downloading datasheet: {str(e)}',
            'data': None
        }), 500

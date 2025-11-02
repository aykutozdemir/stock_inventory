"""
Stocks blueprint
Handles stock-related API endpoints.
"""
import logging
import time
from flask import Blueprint, request, jsonify
from backend.services.stock_service import StockService
from backend.utils.security import sanitize_input
from backend.utils.logger import get_request_logger, log_request

logger = get_request_logger()
stocks_bp = Blueprint('stocks', __name__, url_prefix='/api/stocks')
stock_service = StockService()

@stocks_bp.route('', methods=['GET'])
def get_stocks():
    """Get all stocks with optional category filter"""
    start_time = time.time()

    try:
        category_id = request.args.get('category_id', type=int)
        stocks = stock_service.get_all_stocks(category_id)

        response = jsonify({
            'success': True,
            'message': f'Stocks retrieved successfully ({len(stocks)} items)',
            'data': stocks
        })

        log_request(logger, 'GET', request.path, 200, time.time() - start_time)
        return response

    except Exception as e:
        logger.error(f"Error getting stocks: {e}")
        log_request(logger, 'GET', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@stocks_bp.route('/<int:stock_id>', methods=['GET'])
def get_stock(stock_id):
    """Get stock by ID"""
    start_time = time.time()

    try:
        stock = stock_service.get_stock_by_id(stock_id)

        if stock:
            response = jsonify({
                'success': True,
                'message': 'Stock retrieved successfully',
                'data': stock
            })
            log_request(logger, 'GET', request.path, 200, time.time() - start_time)
            return response
        else:
            response = jsonify({
                'success': False,
                'message': 'Stock not found',
                'data': None
            }), 404
            log_request(logger, 'GET', request.path, 404, time.time() - start_time)
            return response

    except Exception as e:
        logger.error(f"Error getting stock {stock_id}: {e}")
        log_request(logger, 'GET', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@stocks_bp.route('', methods=['POST'])
def create_stock():
    """Create new stock item"""
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

        # Sanitize input
        for field in ['name', 'unit', 'location', 'description']:
            if field in data:
                data[field] = sanitize_input(data[field])

        result = stock_service.create_stock(data)

        status_code = 201 if result['success'] else 400
        response = jsonify(result)
        log_request(logger, 'POST', request.path, status_code, time.time() - start_time)
        return response, status_code

    except Exception as e:
        logger.error(f"Error creating stock: {e}")
        log_request(logger, 'POST', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@stocks_bp.route('/<int:stock_id>', methods=['PUT'])
def update_stock(stock_id):
    """Update stock item"""
    start_time = time.time()

    try:
        data = request.get_json()

        if not data:
            response = jsonify({
                'success': False,
                'message': 'No data provided',
                'data': None
            }), 400
            log_request(logger, 'PUT', request.path, 400, time.time() - start_time)
            return response

        # Sanitize input
        for field in ['name', 'unit', 'location', 'description']:
            if field in data:
                data[field] = sanitize_input(data[field])

        result = stock_service.update_stock(stock_id, data)

        status_code = 200 if result['success'] else 400
        response = jsonify(result)
        log_request(logger, 'PUT', request.path, status_code, time.time() - start_time)
        return response, status_code

    except Exception as e:
        logger.error(f"Error updating stock {stock_id}: {e}")
        log_request(logger, 'PUT', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@stocks_bp.route('/<int:stock_id>', methods=['DELETE'])
def delete_stock(stock_id):
    """Delete stock item"""
    start_time = time.time()

    try:
        result = stock_service.delete_stock(stock_id)

        status_code = 200 if result['success'] else 400
        response = jsonify(result)
        log_request(logger, 'DELETE', request.path, status_code, time.time() - start_time)
        return response, status_code

    except Exception as e:
        logger.error(f"Error deleting stock {stock_id}: {e}")
        log_request(logger, 'DELETE', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@stocks_bp.route('/<int:stock_id>/image', methods=['POST'])
def upload_stock_image(stock_id):
    """Upload image for stock item"""
    start_time = time.time()

    try:
        if 'file' not in request.files:
            response = jsonify({
                'success': False,
                'message': 'No file provided',
                'data': None
            }), 400
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return response

        file = request.files['file']
        if file.filename == '':
            response = jsonify({
                'success': False,
                'message': 'No file selected',
                'data': None
            }), 400
            log_request(logger, 'POST', request.path, 400, time.time() - start_time)
            return response

        result = stock_service.upload_stock_image(stock_id, file)

        status_code = 200 if result['success'] else 400
        response = jsonify(result)
        log_request(logger, 'POST', request.path, status_code, time.time() - start_time)
        return response, status_code

    except Exception as e:
        logger.error(f"Error uploading image for stock {stock_id}: {e}")
        log_request(logger, 'POST', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@stocks_bp.route('/summary', methods=['GET'])
def get_stock_summary():
    """Get stock summary statistics"""
    start_time = time.time()

    try:
        summary = stock_service.get_stock_summary()

        response = jsonify({
            'success': True,
            'message': 'Stock summary retrieved successfully',
            'data': summary
        })

        log_request(logger, 'GET', request.path, 200, time.time() - start_time)
        return response

    except Exception as e:
        logger.error(f"Error getting stock summary: {e}")
        log_request(logger, 'GET', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@stocks_bp.route('/low-stock', methods=['GET'])
def get_low_stock():
    """Get items with low stock"""
    start_time = time.time()

    try:
        threshold = request.args.get('threshold', 5, type=int)
        if threshold < 0:
            threshold = 5

        items = stock_service.get_low_stock_items(threshold)

        response = jsonify({
            'success': True,
            'message': f'Found {len(items)} low stock items',
            'data': items
        })

        log_request(logger, 'GET', request.path, 200, time.time() - start_time)
        return response

    except Exception as e:
        logger.error(f"Error getting low stock items: {e}")
        log_request(logger, 'GET', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

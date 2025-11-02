"""
Categories blueprint
Handles category-related API endpoints.
"""
import logging
from flask import Blueprint, request, jsonify
from backend.services.category_service import CategoryService
from backend.utils.security import sanitize_input
from backend.utils.logger import get_request_logger, log_request
import time

logger = get_request_logger()
categories_bp = Blueprint('categories', __name__, url_prefix='/api/categories')
category_service = CategoryService()

@categories_bp.route('', methods=['GET'])
def get_categories():
    """Get all categories"""
    start_time = time.time()

    try:
        categories = category_service.get_all_categories()

        response = jsonify({
            'success': True,
            'message': 'Categories retrieved successfully',
            'data': categories
        })

        log_request(logger, 'GET', request.path, 200, time.time() - start_time)
        return response

    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        log_request(logger, 'GET', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@categories_bp.route('/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """Get category by ID"""
    start_time = time.time()

    try:
        category = category_service.get_category_by_id(category_id)

        if category:
            response = jsonify({
                'success': True,
                'message': 'Category retrieved successfully',
                'data': category
            })
            log_request(logger, 'GET', request.path, 200, time.time() - start_time)
            return response
        else:
            response = jsonify({
                'success': False,
                'message': 'Category not found',
                'data': None
            }), 404
            log_request(logger, 'GET', request.path, 404, time.time() - start_time)
            return response

    except Exception as e:
        logger.error(f"Error getting category {category_id}: {e}")
        log_request(logger, 'GET', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@categories_bp.route('', methods=['POST'])
def create_category():
    """Create new category"""
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
        if 'name' in data:
            data['name'] = sanitize_input(data['name'])
        if 'description' in data:
            data['description'] = sanitize_input(data['description'])

        result = category_service.create_category(data)

        status_code = 201 if result['success'] else 400
        response = jsonify(result)
        log_request(logger, 'POST', request.path, status_code, time.time() - start_time)
        return response, status_code

    except Exception as e:
        logger.error(f"Error creating category: {e}")
        log_request(logger, 'POST', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@categories_bp.route('/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """Update category"""
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
        if 'name' in data:
            data['name'] = sanitize_input(data['name'])
        if 'description' in data:
            data['description'] = sanitize_input(data['description'])

        result = category_service.update_category(category_id, data)

        status_code = 200 if result['success'] else 400
        response = jsonify(result)
        log_request(logger, 'PUT', request.path, status_code, time.time() - start_time)
        return response, status_code

    except Exception as e:
        logger.error(f"Error updating category {category_id}: {e}")
        log_request(logger, 'PUT', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@categories_bp.route('/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete category"""
    start_time = time.time()

    try:
        result = category_service.delete_category(category_id)

        status_code = 200 if result['success'] else 400
        response = jsonify(result)
        log_request(logger, 'DELETE', request.path, status_code, time.time() - start_time)
        return response, status_code

    except Exception as e:
        logger.error(f"Error deleting category {category_id}: {e}")
        log_request(logger, 'DELETE', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

@categories_bp.route('/search', methods=['GET'])
def search_categories():
    """Search categories by name"""
    start_time = time.time()

    try:
        search_term = request.args.get('q', '').strip()
        limit = request.args.get('limit', 20, type=int)

        # Validate limit
        if limit < 1 or limit > 100:
            limit = 20

        # Sanitize search term
        search_term = sanitize_input(search_term)

        categories = category_service.search_categories(search_term, limit)

        response = jsonify({
            'success': True,
            'message': f'Found {len(categories)} categories',
            'data': categories
        })

        log_request(logger, 'GET', request.path, 200, time.time() - start_time)
        return response

    except Exception as e:
        logger.error(f"Error searching categories: {e}")
        log_request(logger, 'GET', request.path, 500, time.time() - start_time)
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'data': None
        }), 500

"""
Electronic Component Inventory - Main Application
Modular Flask application with blueprints and proper architecture.
"""
import os
import logging
from flask import Flask, send_from_directory, Response
from flask_cors import CORS
from backend.config import get_config
from backend.utils.logger import setup_logger
from backend.models.database import init_database

# Import blueprints
from backend.blueprints.categories import categories_bp
from backend.blueprints.stocks import stocks_bp
from backend.blueprints.conversations import conversations_bp
from backend.blueprints.datasheets import datasheets_bp
from backend.blueprints.ai import ai_bp

# Setup logger
logger = setup_logger()

def create_app(config_name: str = None) -> Flask:
    """
    Application factory pattern
    Creates and configures the Flask application
    """
    app = Flask(__name__)

    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)

    # Setup logging
    app.logger = logger

    # Initialize extensions
    CORS(app, origins=config.CORS_ORIGINS)

    # Register blueprints
    app.register_blueprint(categories_bp)
    app.register_blueprint(stocks_bp)
    app.register_blueprint(conversations_bp)
    app.register_blueprint(datasheets_bp)
    app.register_blueprint(ai_bp)

    # Static file routes
    @app.route('/')
    def index():
        return send_from_directory('../frontend', 'index.html')

    @app.route('/about')
    def about():
        return send_from_directory('../frontend', 'index.html')

    @app.route('/static/css/<path:filename>')
    def static_css(filename):
        return send_from_directory('../frontend/static/css', filename, mimetype='text/css')

    @app.route('/static/js/<path:filename>')
    def static_js(filename):
        return send_from_directory('../frontend/static/js', filename, mimetype='application/javascript')

    @app.route('/static/images/<path:filename>')
    def static_images(filename):
        return send_from_directory('../frontend/static/images', filename)

    # Favicon routes
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory('../frontend/static/favicon', 'favicon.ico', mimetype='image/x-icon')

    @app.route('/favicon-<size>.png')
    def favicon_size(size):
        return send_from_directory('../frontend/static/favicon', f'favicon-{size}.png', mimetype='image/png')

    # Upload file serving
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(config.UPLOAD_FOLDER, filename)

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'version': '2.0.0'}

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found', 'status_code': 404}, 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f'Internal server error: {error}')
        return {'error': 'Internal server error', 'status_code': 500}, 500

    @app.errorhandler(400)
    def bad_request(error):
        return {'error': 'Bad request', 'status_code': 400}, 400

    logger.info(f'Application created with config: {config.__class__.__name__}')
    return app

def main():
    """Main entry point"""
    # Initialize database
    try:
        config = get_config()
        db_path = init_database(config.DATABASE)
        logger.info(f'Database initialized at: {db_path}')
    except Exception as e:
        logger.error(f'Failed to initialize database: {e}')
        return

    # Create and run application
    app = create_app()

    logger.info("=" * 50)
    logger.info("Electronic Component Inventory Server")
    logger.info("=" * 50)
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    logger.info(f"Debug mode: {app.config['DEBUG']}")
    logger.info("Server starting on: http://0.0.0.0:5000")
    logger.info("")
    logger.info("To access from your phone:")
    logger.info("1. Make sure your phone and computer are on the same network")
    logger.info("2. Find your computer's IP: hostname -I")
    logger.info("3. Access from phone: http://YOUR_IP:5000")
    logger.info("=" * 50)

    # Run server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG'],
        use_reloader=app.config['DEBUG']
    )

if __name__ == '__main__':
    main()

import os
from flask import Flask, send_from_directory

from myapp.config.config import load_config
from myapp.adapters.postgres.repository import SupabaseUserRepository, SupabaseDocumentRepository
from myapp.application.services import UserService, DocumentService
from myapp.adapters.http.routes import main_routes, auth_routes, document_routes, api_routes, init_routes
from myapp.metrics.logger import timed, metrics_logger, app_logger


def create_app():
    """Create and configure the Flask application"""
    # Load configuration
    app_config, db_config = load_config()
    
    # Ensure static folder exists
    if not os.path.exists(app_config.static_folder):
        os.makedirs(app_config.static_folder)
    
    # Create Flask app
    app = Flask(
        __name__,
        static_folder=app_config.static_folder,
        template_folder=app_config.templates_folder
    )
    
    # Configure Flask
    app.secret_key = app_config.secret_key
    app.debug = app_config.debug
    
    # Create repositories
    user_repository = SupabaseUserRepository(db_config.supabase_url, db_config.supabase_key)
    document_repository = SupabaseDocumentRepository(db_config.supabase_url, db_config.supabase_key)
    
    # Create services
    user_service = UserService(user_repository)
    document_service = DocumentService(document_repository)
    
    # Initialize routes
    init_routes(user_service, document_service)
    
    # Register blueprints
    app.register_blueprint(main_routes)
    app.register_blueprint(auth_routes, url_prefix='/auth')
    app.register_blueprint(document_routes, url_prefix='/document')
    app.register_blueprint(api_routes, url_prefix='/api')
    
    # Add special routes
    
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """Serve static files"""
        return send_from_directory(app_config.static_folder, filename)
    
    @app.route('/favicon.ico')
    def favicon():
        """Serve favicon"""
        return send_from_directory(os.path.join(app_config.static_folder, 'img'), 'favicon.ico')
    
    @app.route('/examples/<example_name>')
    def get_example(example_name):
        """Serve example documents"""
        examples_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'examples')
        if not os.path.exists(examples_dir):
            os.makedirs(examples_dir)
        return send_from_directory(examples_dir, f"{example_name}.json")
    
    @app.route('/metrics')
    def view_metrics():
        """View application metrics"""
        return metrics_logger.get_metrics()
    
    # Log application startup
    app_logger.info("Application started")
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000) 
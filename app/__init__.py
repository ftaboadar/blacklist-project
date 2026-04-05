"""
Flask Application Factory
"""
import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restful import Api
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
ma = Marshmallow()
jwt = JWTManager()


def create_app(config_name=None):
    app = Flask(__name__)

    # Database configuration
    if config_name == 'testing':
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        app.config['TESTING'] = True
    else:
        db_user = os.environ.get('RDS_USERNAME', 'postgres')
        db_password = os.environ.get('RDS_PASSWORD', 'postgres')
        db_host = os.environ.get('RDS_HOSTNAME', 'localhost')
        db_port = os.environ.get('RDS_PORT', '5432')
        db_name = os.environ.get('RDS_DB_NAME', 'blacklist_db')

        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
        )

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PROPAGATE_EXCEPTIONS'] = True

    # JWT Configuration - Token estático para simplicidad
    app.config['JWT_SECRET_KEY'] = os.environ.get(
        'JWT_SECRET_KEY', 'super-secret-key-devops-2024'
    )

    # Initialize extensions
    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)

    # JWT error handlers - return JSON instead of HTML
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'message': 'Token has expired', 'error': 'token_expired'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'message': 'Invalid token', 'error': 'invalid_token'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'message': 'Missing authorization token', 'error': 'authorization_required'}), 401

    # Register API resources
    api = Api(app)

    from app.resources import BlacklistResource, BlacklistCheckResource, HealthCheckResource

    api.add_resource(BlacklistResource, '/blacklists')
    api.add_resource(BlacklistCheckResource, '/blacklists/<string:email>')
    api.add_resource(HealthCheckResource, '/')

    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'message': 'Resource not found', 'error': 'not_found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'message': 'Internal server error', 'error': 'server_error'}), 500

    # Create tables
    with app.app_context():
        db.create_all()

    return app

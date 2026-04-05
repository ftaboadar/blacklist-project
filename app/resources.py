"""
Resources - API REST Endpoints
"""
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError

from app import db
from app.models import BlacklistEntry
from app.schemas import BlacklistCreateSchema, BlacklistResponseSchema

blacklist_create_schema = BlacklistCreateSchema()
blacklist_response_schema = BlacklistResponseSchema()


class HealthCheckResource(Resource):
    """Health check endpoint for AWS Elastic Beanstalk"""

    def get(self):
        return {'status': 'healthy', 'service': 'blacklist-api'}, 200


class BlacklistResource(Resource):
    """POST /blacklists - Add an email to the global blacklist"""

    @jwt_required()
    def post(self):
        # Validate request body
        try:
            data = blacklist_create_schema.load(request.get_json())
        except ValidationError as err:
            return {'errors': err.messages}, 400

        # Get client IP address (X-Forwarded-For is set by AWS ALB)
        forwarded_for = request.headers.get('X-Forwarded-For', '')
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs: client, proxy1, proxy2
            ip_address = forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.remote_addr or '0.0.0.0'

        # Create new blacklist entry
        new_entry = BlacklistEntry(
            email=data['email'],
            app_uuid=data['app_uuid'],
            blocked_reason=data.get('blocked_reason'),
            ip_address=ip_address
        )

        db.session.add(new_entry)
        db.session.commit()

        return {
            'message': f"Email '{data['email']}' has been added to the global blacklist successfully."
        }, 201


class BlacklistCheckResource(Resource):
    """GET /blacklists/<email> - Check if an email is blacklisted"""

    @jwt_required()
    def get(self, email):
        entry = BlacklistEntry.query.filter_by(email=email).first()

        if entry:
            return blacklist_response_schema.dump({
                'is_blacklisted': True,
                'blocked_reason': entry.blocked_reason
            }), 200
        else:
            return blacklist_response_schema.dump({
                'is_blacklisted': False,
                'blocked_reason': None
            }), 200

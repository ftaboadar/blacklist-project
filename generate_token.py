"""
Utility to generate a JWT token for testing.
Run: python generate_token.py
"""
import os
from app import create_app
from flask_jwt_extended import create_access_token

app = create_app()

with app.app_context():
    token = create_access_token(identity='test-user')
    print("\n=== JWT Token for Testing ===")
    print(f"Bearer {token}")
    print("\nUse in Postman or curl:")
    print(f'  Authorization: Bearer {token}\n')

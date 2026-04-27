"""
Tests - Blacklist API
Run with: python -m pytest tests/ -v
"""
import pytest
from flask_jwt_extended import create_access_token
from app import create_app, db


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_headers(app):
    """Generate valid JWT auth headers."""
    with app.app_context():
        token = create_access_token(identity='test-user')
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }


class TestHealthCheck:
    """Tests for GET / (health check)."""

    def test_health_check_returns_200(self, client):
        response = client.get('/')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'blacklist-api'


class TestPostBlacklist:
    """Tests for POST /blacklists."""

    def test_add_email_success(self, client, auth_headers):
        payload = {
            'email': 'spam@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000',
            'blocked_reason': 'Spam recurrente'
        }
        response = client.post('/blacklists', json=payload, headers=auth_headers)
        assert response.status_code == 201
        data = response.get_json()
        assert 'spam@example.com' in data['message']

    def test_add_email_without_reason(self, client, auth_headers):
        payload = {
            'email': 'test@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000'
        }
        response = client.post('/blacklists', json=payload, headers=auth_headers)
        assert response.status_code == 201

    def test_add_email_missing_app_uuid(self, client, auth_headers):
        payload = {
            'email': 'test@example.com'
        }
        response = client.post('/blacklists', json=payload, headers=auth_headers)
        assert response.status_code == 400
        data = response.get_json()
        assert 'app_uuid' in data['errors']

    def test_add_email_invalid_format(self, client, auth_headers):
        payload = {
            'email': 'not-an-email',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000'
        }
        response = client.post('/blacklists', json=payload, headers=auth_headers)
        assert response.status_code == 400
        data = response.get_json()
        assert 'email' in data['errors']

    def test_add_email_reason_too_long(self, client, auth_headers):
        payload = {
            'email': 'test@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000',
            'blocked_reason': 'x' * 256
        }
        response = client.post('/blacklists', json=payload, headers=auth_headers)
        assert response.status_code == 400

    def test_add_email_no_auth(self, client):
        payload = {
            'email': 'test@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000'
        }
        response = client.post('/blacklists', json=payload,
                               headers={'Content-Type': 'application/json'})
        assert response.status_code == 401

    def test_add_email_empty_body(self, client, auth_headers):
        response = client.post('/blacklists', json={}, headers=auth_headers)
        assert response.status_code == 400


class TestGetBlacklist:
    """Tests for GET /blacklists/<email>."""

    def test_check_blacklisted_email(self, client, auth_headers):
        # First, add an email
        payload = {
            'email': 'blocked@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000',
            'blocked_reason': 'Motivo de prueba'
        }
        client.post('/blacklists', json=payload, headers=auth_headers)

        # Then check it
        response = client.get('/blacklists/blocked@example.com', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['is_blacklisted'] is True
        assert data['blocked_reason'] == 'Motivo de prueba'

    def test_check_non_blacklisted_email(self, client, auth_headers):
        response = client.get('/blacklists/clean@example.com', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['is_blacklisted'] is False
        assert data['blocked_reason'] is None

    def test_check_email_no_auth(self, client):
        response = client.get('/blacklists/test@example.com')
        assert response.status_code == 401

    def test_check_email_without_reason(self, client, auth_headers):
        # Add email without blocked_reason
        payload = {
            'email': 'noreason@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000'
        }
        client.post('/blacklists', json=payload, headers=auth_headers)

        response = client.get('/blacklists/noreason@example.com', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data['is_blacklisted'] is True
        assert data['blocked_reason'] is None


class TestErrorHandlers:
    """Tests for global error handlers and edge cases."""

    def test_404_returns_json(self, client):
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404
        data = response.get_json()
        assert data['error'] == 'not_found'

    def test_invalid_token_returns_json(self, client):
        headers = {
            'Authorization': 'Bearer invalid-token-here',
            'Content-Type': 'application/json'
        }
        response = client.get('/blacklists/test@example.com', headers=headers)
        assert response.status_code == 401 or response.status_code == 422

    def test_ip_from_x_forwarded_for(self, client, auth_headers, app):
        """Verify IP is captured from X-Forwarded-For header (AWS ALB)."""
        auth_headers['X-Forwarded-For'] = '203.0.113.50, 70.41.3.18'
        payload = {
            'email': 'iptest@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000'
        }
        client.post('/blacklists', json=payload, headers=auth_headers)

        from app.models import BlacklistEntry
        with app.app_context():
            entry = BlacklistEntry.query.filter_by(email='iptest@example.com').first()
            assert entry is not None
            assert entry.ip_address == '203.0.113.50'

    def test_duplicate_email_returns_400(self, client, auth_headers):
        """Duplicate email in same blacklist is rejected."""
        payload1 = {
            'email': 'dup@example.com',
            'app_uuid': 'uuid-app-1',
            'blocked_reason': 'App 1'
        }
        payload2 = {
            'email': 'dup@example.com',
            'app_uuid': 'uuid-app-2',
            'blocked_reason': 'App 2'
        }
        r1 = client.post('/blacklists', json=payload1, headers=auth_headers)
        r2 = client.post('/blacklists', json=payload2, headers=auth_headers)
        assert r1.status_code == 201
        assert r2.status_code == 400
        data = r2.get_json()
        assert 'dup@example.com' in data['message']

    def test_stored_fields_are_correct(self, client, auth_headers, app):
        """Verify all fields are stored correctly in DB."""
        payload = {
            'email': 'verify@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000',
            'blocked_reason': 'Test reason'
        }
        client.post('/blacklists', json=payload, headers=auth_headers)

        from app.models import BlacklistEntry
        with app.app_context():
            entry = BlacklistEntry.query.filter_by(email='verify@example.com').first()
            assert entry is not None
            assert entry.email == 'verify@example.com'
            assert entry.app_uuid == '550e8400-e29b-41d4-a716-446655440000'
            assert entry.blocked_reason == 'Test reason'
            assert entry.ip_address is not None
            assert entry.created_at is not None


class TestPostBlacklistEdgeCases:
    """Additional edge-case tests for POST /blacklists."""

    def test_add_email_missing_email_field(self, client, auth_headers):
        payload = {'app_uuid': '550e8400-e29b-41d4-a716-446655440000'}
        response = client.post('/blacklists', json=payload, headers=auth_headers)
        assert response.status_code == 400
        data = response.get_json()
        assert 'email' in data['errors']

    def test_add_email_blocked_reason_exactly_255_chars(self, client, auth_headers):
        payload = {
            'email': 'boundary@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000',
            'blocked_reason': 'x' * 255
        }
        response = client.post('/blacklists', json=payload, headers=auth_headers)
        assert response.status_code == 201

    def test_add_email_blocked_reason_256_chars_rejected(self, client, auth_headers):
        payload = {
            'email': 'toolong@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000',
            'blocked_reason': 'x' * 256
        }
        response = client.post('/blacklists', json=payload, headers=auth_headers)
        assert response.status_code == 400

    def test_add_email_response_contains_email_in_message(self, client, auth_headers):
        payload = {
            'email': 'msgcheck@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000'
        }
        response = client.post('/blacklists', json=payload, headers=auth_headers)
        assert response.status_code == 201
        data = response.get_json()
        assert 'message' in data
        assert 'msgcheck@example.com' in data['message']

    def test_add_email_invalid_bearer_format(self, client):
        headers = {
            'Authorization': 'Token not-a-bearer',
            'Content-Type': 'application/json'
        }
        payload = {
            'email': 'test@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000'
        }
        response = client.post('/blacklists', json=payload, headers=headers)
        assert response.status_code in (401, 422)

    def test_add_email_ip_fallback_when_no_forwarded_header(self, client, auth_headers, app):
        payload = {
            'email': 'fallbackip@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000'
        }
        client.post('/blacklists', json=payload, headers=auth_headers)

        from app.models import BlacklistEntry
        with app.app_context():
            entry = BlacklistEntry.query.filter_by(email='fallbackip@example.com').first()
            assert entry is not None
            assert entry.ip_address is not None


class TestGetBlacklistEdgeCases:
    """Additional edge-case tests for GET /blacklists/<email>."""

    def test_check_returns_json_content_type(self, client, auth_headers):
        response = client.get('/blacklists/anyemail@example.com', headers=auth_headers)
        assert 'application/json' in response.content_type

    def test_check_blacklisted_response_structure(self, client, auth_headers):
        payload = {
            'email': 'structure@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000',
            'blocked_reason': 'Reason check'
        }
        client.post('/blacklists', json=payload, headers=auth_headers)
        response = client.get('/blacklists/structure@example.com', headers=auth_headers)
        data = response.get_json()
        assert 'is_blacklisted' in data
        assert 'blocked_reason' in data

    def test_check_not_blacklisted_response_structure(self, client, auth_headers):
        response = client.get('/blacklists/nothere@example.com', headers=auth_headers)
        data = response.get_json()
        assert 'is_blacklisted' in data
        assert 'blocked_reason' in data
        assert data['is_blacklisted'] is False
        assert data['blocked_reason'] is None

    def test_check_after_add_is_blacklisted_true(self, client, auth_headers):
        email = 'roundtrip@example.com'
        client.post('/blacklists', json={
            'email': email,
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000'
        }, headers=auth_headers)
        response = client.get(f'/blacklists/{email}', headers=auth_headers)
        assert response.get_json()['is_blacklisted'] is True


class TestModelAndSchema:
    """Tests for the model and schema layer."""

    def test_blacklistentry_repr(self, app):
        from app.models import BlacklistEntry
        with app.app_context():
            entry = BlacklistEntry(
                email='repr@example.com',
                app_uuid='uuid-1'
            )
            assert 'repr@example.com' in repr(entry)

    def test_blacklistentry_created_at_set_automatically(self, client, auth_headers, app):
        from app.models import BlacklistEntry
        client.post('/blacklists', json={
            'email': 'autotime@example.com',
            'app_uuid': '550e8400-e29b-41d4-a716-446655440000'
        }, headers=auth_headers)
        with app.app_context():
            entry = BlacklistEntry.query.filter_by(email='autotime@example.com').first()
            assert entry.created_at is not None

    def test_schema_invalid_email_raises_error(self):
        from app.schemas import BlacklistCreateSchema
        from marshmallow import ValidationError
        schema = BlacklistCreateSchema()
        with pytest.raises(ValidationError):
            schema.load({'email': 'not-valid', 'app_uuid': 'uuid-1'})

    def test_schema_valid_data_loads_correctly(self):
        from app.schemas import BlacklistCreateSchema
        schema = BlacklistCreateSchema()
        result = schema.load({
            'email': 'valid@example.com',
            'app_uuid': 'uuid-1',
            'blocked_reason': 'Some reason'
        })
        assert result['email'] == 'valid@example.com'
        assert result['blocked_reason'] == 'Some reason'

    def test_schema_blocked_reason_defaults_to_none(self):
        from app.schemas import BlacklistCreateSchema
        schema = BlacklistCreateSchema()
        result = schema.load({'email': 'valid@example.com', 'app_uuid': 'uuid-1'})
        assert result['blocked_reason'] is None


class TestForzarFallo:
    """Test temporal para verificar que el pipeline se detiene ante fallos."""

    def test_fallo_intencional(self):
        assert False, "FALLO INTENCIONAL - eliminar este test antes del merge"

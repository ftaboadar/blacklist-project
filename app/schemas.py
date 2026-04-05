"""
Schemas - Marshmallow validation and serialization
"""
from marshmallow import Schema, fields, validate


class BlacklistCreateSchema(Schema):
    email = fields.Email(required=True)
    app_uuid = fields.Str(required=True)
    blocked_reason = fields.Str(
        required=False,
        load_default=None,
        validate=validate.Length(max=255)
    )


class BlacklistResponseSchema(Schema):
    is_blacklisted = fields.Bool(required=True)
    blocked_reason = fields.Str(allow_none=True)

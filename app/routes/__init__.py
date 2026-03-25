from .auth               import bp as auth_bp
from .identity_records   import bp as identity_records_bp
from .data_users         import bp as data_users_bp
from .data_providers     import bp as data_providers_bp
from .webhooks           import bp as webhooks_bp
from .portal_dcc         import bp as portal_dcc_bp
from .admin              import bp as admin_bp
from .self_service       import bp as self_service_bp

__all__ = [
    "auth_bp", "identity_records_bp", "data_users_bp", "data_providers_bp",
    "webhooks_bp", "portal_dcc_bp", "admin_bp", "self_service_bp",
]

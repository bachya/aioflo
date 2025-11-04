"""Define package constants."""
# API Base URLs
API_V1_BASE: str = "https://api.meetflo.com/api/v1"
API_V2_BASE: str = "https://api-gw.meetflo.com/api/v2"

# OAuth2 Configuration
# These are shared application credentials used by the Moen Flo mobile/web app
OAUTH2_CLIENT_ID: str = "3baec26f-0e8b-4e1d-84b0-e178f05ea0a5"
OAUTH2_CLIENT_SECRET: str = "3baec26f-0e8b-4e1d-84b0-e178f05ea0a5"
OAUTH2_TOKEN_ENDPOINT: str = "https://api-gw.meetflo.com/api/v1/oauth2/token"
OAUTH2_GRANT_TYPE_PASSWORD: str = "password"
OAUTH2_GRANT_TYPE_REFRESH: str = "refresh_token"

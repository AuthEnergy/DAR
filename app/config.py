import os

class Config:
    # CouchDB
    COUCHDB_URL      = os.getenv("COUCHDB_URL",      "http://localhost:5984")
    COUCHDB_USER     = os.getenv("COUCHDB_USER",     "admin")
    COUCHDB_PASSWORD = os.getenv("COUCHDB_PASSWORD", "password")

    # JWT
    JWT_SECRET       = os.getenv("JWT_SECRET",       "change-me-in-production")
    JWT_EXPIRY_SEC   = int(os.getenv("JWT_EXPIRY_SEC", 7200))

    # Portal
    PORTAL_BASE_URL  = os.getenv("PORTAL_BASE_URL",  "https://portal.central.consent")

    # App
    DEBUG            = os.getenv("DEBUG", "false").lower() == "true"
    API_VERSION      = "v1"

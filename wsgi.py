"""WSGI entry point — Apache mod_wsgi and local dev."""
from app.factory import create_app

application = create_app()

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000, debug=True)

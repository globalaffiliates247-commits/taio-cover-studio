"""
wsgi.py - Điểm vào WSGI cho Gunicorn trên production / Docker container.
"""

from web.server import app

if __name__ == "__main__":
    app.run()

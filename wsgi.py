"""WSGI entry point."""
from auto_recon_app.app import create_app

app = create_app()

if __name__ == '__main__':
    app.run() 
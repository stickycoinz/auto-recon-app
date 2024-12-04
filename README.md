# Auto Recon Management System

A streamlined vehicle reconditioning management system built with Flask and SQLAlchemy.

## Features

- **Vehicle Management**: Track vehicles through the reconditioning process
- **Service Management**: Manage reconditioning services with customizable pricing
- **Workflow Board**: Visual kanban-style board for tracking vehicle status
- **User Management**: Role-based access control (Corporate and Ground Manager)
- **Dealership Management**: Multi-dealership support with custom service pricing
- **Reporting**: Basic analytics and financial reporting

## Project Structure

```
auto_recon/
├── auto_recon_app/
│   ├── __init__.py
│   ├── app.py              # Main application file
│   ├── models.py           # Database models
│   ├── extensions.py       # Flask extensions
│   ├── static/             # Static files (CSS, JS, images)
│   └── templates/          # Jinja2 templates
├── migrations/             # Database migrations
├── instance/              # Instance-specific files
├── .env                   # Environment variables (create this)
├── requirements.txt       # Project dependencies
├── setup_db.py           # Database initialization script
└── README.md             # This file
```

## Setup

1. Create a Python virtual environment:
```bash
python -m venv .venv
```

2. Activate the virtual environment:
```bash
# Windows
.venv\Scripts\activate

# Unix/MacOS
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with the following content:
```
FLASK_APP=auto_recon_app.app
FLASK_DEBUG=1
SECRET_KEY=your-secret-key-here
WTF_CSRF_SECRET_KEY=your-csrf-secret-key
```

5. Initialize the database:
```bash
python setup_db.py
```

6. Run the application:
```bash
flask run
```

7. Access the application at `http://localhost:5000`
   - Default admin credentials:
     - Username: `admin`
     - Password: `admin`

## Development

### Database Migrations

When making changes to models:

1. Generate migration:
```bash
flask db migrate -m "Description of changes"
```

2. Apply migration:
```bash
flask db upgrade
```

### Project Guidelines

- Keep routes and views in `app.py`
- Database models in `models.py`
- Flask extensions in `extensions.py`
- Use type hints and docstrings
- Follow PEP 8 style guide
- Write unit tests for new features

## Security

- CSRF protection enabled
- Password hashing using Werkzeug
- Role-based access control
- Input validation and sanitization
- Rate limiting on authentication endpoints

## License

MIT License - See LICENSE file for details

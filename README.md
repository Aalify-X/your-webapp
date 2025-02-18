# Progrify Web Application

## Deployment Configuration
- Python Version: 3.11.9
- Backend Framework: Flask
- Deployment Platform: Render

## Local Setup
1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate venv: `source venv/bin/activate` (Unix) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Run application: `gunicorn backend.app:app`

## Environment Variables
- `FLASK_ENV`: Set to `production` for deployment
- `SECRET_KEY`: Generated during deployment
- `PORT`: Default 10000

## Deployment Notes
- Uses gunicorn as WSGI server
- Serves backend and frontend from same application
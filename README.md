# Aalify-X Web Application

## Prerequisites
- Python 3.9+
- pip (Python package manager)
- Virtual Environment (recommended)

## Setup Instructions

1. Clone the repository
```bash
git clone https://github.com/yourusername/aalify-x.git
cd aalify-x
```

2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install Dependencies
```bash
pip install -r requirements.txt
```

4. Download SpaCy Language Model
```bash
python -m spacy download en_core_web_sm
```

5. Set Environment Variables
Create a `.env` file in the project root with:
```
SECRET_KEY=your_secret_key_here
FLASK_ENV=development
```

6. Run the Application
```bash
python app.py
```

## Features
- Document Intelligence
- Smart Flashcards
- Learning Analytics
- Digital Canvas

## Troubleshooting
- Ensure all dependencies are installed
- Check Python version compatibility
- Verify virtual environment activation

## Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the LICENSE.md file for details.

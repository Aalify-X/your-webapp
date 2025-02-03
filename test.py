from flask import Flask, render_template_string
import os

app = Flask(__name__)

@app.route('/')
def index():
    # Super simple HTML template
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1>Hello World</h1>
        <p>This is a test page</p>
        <pre>
        Template folder: {{ template_folder }}
        Files in template folder:
        {{ files }}
        </pre>
    </body>
    </html>
    """
    
    # Get list of template files
    template_folder = app.template_folder
    files = os.listdir(template_folder) if os.path.exists(template_folder) else 'No template folder!'
    
    return render_template_string(html, template_folder=template_folder, files=files)

if __name__ == '__main__':
    app.run(debug=True, port=5000) 
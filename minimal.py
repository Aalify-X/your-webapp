from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    # Simple inline template
    template = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <h1>Hello World</h1>
        </body>
    </html>
    """
    return render_template_string(template)

if __name__ == '__main__':
    print("Starting minimal Flask app...")
    app.run(debug=True, port=5000) 
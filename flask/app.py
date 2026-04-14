from flask import Flask, render_template
import os

# Initialize Flask. 
# We set 'template_folder' to '../templates' because the folder is outside 
# the 'flask' directory and located at the project root.
app = Flask(__name__, template_folder='../templates')

# Routing: This decorator tells Flask to execute the 'index' function
# when the user visits the root URL ('/').
@app.route('/')
def index():
    # render_template looks in the templates folder for 'frontend.html'
    # and returns its content to the user's browser.
    return render_template('frontend.html')

if __name__ == '__main__':
    # Start the development server on all network interfaces at port 5000.
    # 'debug=True' allows the server to automatically reload when code changes.
    app.run(host='0.0.0.0', port=5000, debug=True) 
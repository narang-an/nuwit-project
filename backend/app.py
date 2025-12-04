from flask import Flask, request
import os

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'uploads'

@app.route('/')
def home():
    return "Hello, Flask!"

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('image')

    if not file:
        return {"success": False, "message": "No image uploaded"}

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    return {
        "success": True,
        "filename": file.filename,
        "message": "Uploaded successfully"
    }

if __name__ == '__main__':
    app.run(debug=True)
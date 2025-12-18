from flask import Flask
from flask import jsonify, request, send_from_directory
from flask_cors import CORS
import os

UPLOAD_DIR = "uploads"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.environ.get("CLOSET_UPLOAD_DIR",
                            os.path.join(BASE_DIR, "uploads"))
# since i havent set CLOSET_UPLOAD_DIR, this will be backend/uploads
os.makedirs(UPLOAD_DIR, exist_ok=True)

# debugging
# print("UPLOAD_DIR:", UPLOAD_DIR, "Writable?", os.access(UPLOAD_DIR, os.W_OK))

app = Flask(__name__)

# enable CORS so Streamlit (runs on different port)
# can call this API
CORS(app)

# debugging

"""
@app.before_request
def log_request_info():
    try:
        print(f">>> Incoming {request.method} {request.path}")
        # Only log keys; bodies can be large
        print(">>> Form keys:", list(request.form.keys()))
        print(">>> Files keys:", list(request.files.keys()))
    except Exception as e:
        print(">>> log_request_info error:", e)

@app.after_request
def log_response_info(response):
    try:
        print(f"<<< Responded {response.status_code} {request.path}")
    except Exception as e:
        print("<<< log_response_info error:", e)
    return response
"""


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)

@app.route("/uploads", methods=["POST"])
def upload():
    """
    Accepts multipart/form-data
    - file: image file
    - category: string (Top/Bottom/Shoes/Accessory)
    Saves file into backend/uploads as <Category>___<OriginalName>
    """

    file = request.files.get("file")
    category = request.form.get("category")

    if not file:
        return jsonify({"success": False, "error": "Missing file"}), 400
    if not category:
        return jsonify({"success": False, "error": "Missing category"}), 400
    
    base_name = os.path.basename(file.filename)
    save_name = f"{category}___{base_name}"
    save_path = os.path.join(UPLOAD_DIR, save_name)

    # save to backend/uploads
    file.save(save_path)

    return jsonify({"success": True, "filename": save_name})

def extract_category_from_filename(filename: str):
    """
    We use the convention: <Category>___<OriginalName>.<ext>
    Returns the category if present; otherwise None.
    """
    if "___" in filename:
        return filename.split("___")[0]
    return None


@app.route('/')
def home():
    return "Hello, Flask!"

@app.route("/get_clothes", methods=['GET'])
def get_clothes():
    """
    GET /get_clothes?category=Top
    - If category is not provided, return all uploaded clothes.
    - If category is provided, only return files with that category in the name
    Response JSON:
    {
        "success": true,
        "category": "<category or null>",
        "files": ["Top___shirt1.jpg", "Top___shirt2.png"]
        }
    """
    # i think when the request is sent here, flask automatically knows 
    category = request.args.get("category", default=None, type=str)
    all_files = []
    try:
        for fname in os.listdir(UPLOAD_DIR):
            # only include image-like files
            if fname.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                all_files.append(fname)
    except FileNotFoundError:
        # If folder doesn't exist yet
        all_files = []

    if category:
        files = [f for f in all_files if extract_category_from_filename(f) == category]
    else:
        files = all_files

    return jsonify({
        "success": True,
        "category": category if category else None,
        "files": files
    })

if __name__ == '__main__':
    app.run(debug=True)
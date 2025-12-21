from flask import Flask
from flask import jsonify, request, send_from_directory
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime
from flask import g

# paths
UPLOAD_DIR = "uploads"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.environ.get("CLOSET_UPLOAD_DIR",
                            os.path.join(BASE_DIR, "uploads"))
# since i havent set CLOSET_UPLOAD_DIR, this will be backend/uploads
DP_PATH = os.environ.get("CLOSET_DB_PATH", 
                         os.path.join(BASE_DIR, "closet.db"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

# debugging
# print("UPLOAD_DIR:", UPLOAD_DIR, "Writable?", os.access(UPLOAD_DIR, os.W_OK))

app = Flask(__name__)
# enable CORS so Streamlit (runs on different port) can call this API
CORS(app, resources={r"/*": {"origins": "*"}})

# debugging logging of requests and responses

@app.before_request
def log_request_info():
    print(f">>> {request.method} {request.path} query={dict(request.args)}")


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

#DB helpers
def get_conn():
    conn = sqlite3.connect(DP_PATH, timeout=5)  # wait up to 5s if busy
    conn.row_factory = sqlite3.Row
    # Reduce write locking in dev
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")  # milliseconds
        conn.execute("PRAGMA synchronous = NORMAL;")
    except Exception:
        # Pragmas may fail on some platforms; ignore
        pass
    return conn


def init_db():
    """
    Tables
    - clothing_items(id, filename: unique, category: opt)
    - outfits(id, outfit_name, created_at)
    - outfit_items(id, outfit_id, clothing_item_id, category)
    Indexes:
    - outfit_items(outfit_id)
    - clothing_items(category)
    """

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
                CREATE TABLE IF NOT EXISTS clothing_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE,
                    category TEXT
                )
            """)
    cur.execute("""
                CREATE TABLE IF NOT EXISTS outfits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    outfit_name TEXT,
                    created_at TEXT
                )
            """)
    cur.execute("""
                CREATE TABLE IF NOT EXISTS outfit_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    outfit_id INTEGER,
                    clothing_item_id INTEGER,
                    category TEXT,
                    FOREIGN KEY (outfit_id) REFERENCES outfits(id),
                    FOREIGN KEY (clothing_item_id) REFERENCES clothing_items(id)
            )
        """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_outfit_items_outfit_id ON outfit_items(outfit_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_clothing_items_category ON clothing_items(category)")
    conn.commit()
    conn.close()

def ensure_clothing_item(cur: sqlite3.Cursor, filename: str, assumed_category: str | None):
    """
    Ensure clothing_items has a row for this filename; return id
    Uses the caller's cursor/connection to avoid extra connections/locks.
    """
    category = assumed_category or extract_category_from_filename(filename)
    cur.execute("SELECT id FROM clothing_items WHERE filename = ?", (filename,))
    row = cur.fetchone()
    if row:
        cid = row['id']
    else:
        cur.execute("INSERT INTO clothing_items (filename, category) VALUES (?, ?)", (filename, category))
        cid = cur.lastrowid
    return cid

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

@app.route("/get_clothes", methods=['GET']) # methods = GET is for retrieving data
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

@app.route("/save_outfit", methods=["POST"]) #methods = POST is for sending data to server
def save_outfit():
    """
    POST / save_outfit
    Body JSON: (so this is what it accepts I believe)
    {
        "outfit_name": "Cozy Fall Fit", #optional
        "clothing_items": 
        {
            "Top": ["Top___shirt.jpg", ...],
            "Bottom": ["Bottom___jeans.png", ...],
            "Shoes": [...],
            "Accessory": []
        }
    }
    """
    payload = request.get_json(silent=True) or {}
    outfit_name = payload.get("outfit_name")
    items_grouped = payload.get("clothing_items") or payload.get("items")

    if not isinstance(items_grouped, dict):
        return jsonify({"success": False, "error": "Missing 'clothing_items' dictionary"}), 400
    
    total_count = sum(len(v) for v in items_grouped.values() if isinstance(v, list))
    if total_count == 0:
        return jsonify({"success": False, "error": "No clothing items provided"}), 400
    
    # Create outfit
    created_at = datetime.utcnow().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO outfits(outfit_name, created_at) VALUES (?, ?)", 
                (outfit_name, created_at))
    outfit_id = cur.lastrowid

    # Link items
    for category, filenames in items_grouped.items():
        if not isinstance(filenames, list):
            continue
        for filename in filenames:
            cid = ensure_clothing_item(cur, filename, assumed_category=category)
            cur.execute("INSERT INTO outfit_items (outfit_id, clothing_item_id, category) VALUES (?, ?, ?)",
                        (outfit_id, cid, category))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True,
                    "outfit_id": outfit_id,
                    "outfit_name": outfit_name,
                    "created_at": created_at
                    })

@app.route("/get_outfits", methods=["GET"])
def get_outfits():
    """
    Purpose: Fetch list of all saved outfits from the database.
    Behavior: 
    - Queries the 'outfits' table for id, outfit_name, and created_at.
    - Sorts outfits in descending order by id (newest first).
    Response JSON:
    { "success": True, "outfits: [
        {"id": 1, "outfit_name": "Casual Day", "created_at": "2024-06-01T12:00:00"},
        ...]}

    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, outfit_name, created_at FROM outfits ORDER BY id DESC")
    outfits = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify({"success": True, "outfits": outfits})

@app.route("/get_outfit_items", methods = ["GET"])
def get_outfit_items():
    """
    GET /get_outfit_items?outfit_id=1
    Response JSON:
    {
        "success": True,
        "outfit_id": 1,
        "items": {
            "Top": ["Top___shirt1.jpg", ...],
            "Bottom": [...],
            ...
        }
    }
    """
    outfit_id = request.args.get("outfit_id", type=int)
    if not outfit_id:
        return jsonify({"success": False, "error": "Missing_outfit_id"}), 400
    
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
                SELECT oi.category, ci.filename, ci.id AS clothing_item_id
                FROM outfit_items oi
                JOIN clothing_items ci ON oi.clothing_item_id = ci.id
                WHERE oi.outfit_id = ?
                ORDER BY oi.id ASC
                
                """, (outfit_id,))
    rows = cur.fetchall()
    conn.close()

    grouped = {"Top": [],
               "Bottom": [],
               "Shoes": [],
               "Accessory": []}
    for r in rows:
        grouped.setdefault(r["category"], []).append({
            "filename": r["filename"],
            "clothing_item_id": r["clothing_item_id"]
        })
    
    return jsonify({"success": True, "outfit_id": outfit_id, "items": grouped})

@app.route("/delete_clothing", methods=["DELETE"])
def delete_clothing():
    """
    DELETE /delete_clothing?filename=<fname>&category=,cat.&force=<true|false>
    - filename: required
    - category: optional
    - force: if true, cascade-remove outfits that use this item
    """
    # we've previously only used request.args but we may neen JSON if we do more complex deletes later
    filename = request.args.get("filename", type=str) 
    category = request.args.get("category", type=str)
    force = str(request.args.get("force", "false")).strip().lower() == "true"

    if not filename:
        return jsonify({"success": False, "error": "Missing filename"}), 400
    
    # DB operations
    conn = get_conn()
    cur = conn.cursor()

    # find clothing_item row (may not exist if never used in an outfit)
    cur.execute("SELECT id FROM clothing_items WHERE filename =?", (filename,))
    row = cur.fetchone()
    clothing_item_id = row["id"] if row else None

    # if present in DB, check referencing outfits
    if clothing_item_id is not None:
        cur.execute("""
                    SELECT DISTINCT outfit_id
                    FROM outfit_items
                    WHERE clothing_item_id = ?
                    """, (clothing_item_id,))
        references = [r["outfit_id"] for r in cur.fetchall()]
        if references and not force:
            conn.close()
            return jsonify({
                            "error": "Item is used in outfits",
                            "outfit_ids": references
                            }), 409

        # Cascade remove references if needed
        if references:
            cur.execute("DELETE FROM clothing_items WHERE id=?", (clothing_item_id,))
        cur.execute("DELETE FROM clothing_items where id=?", (clothing_item_id,))
        conn.commit()
    conn.close()

    # delete physical file from uploads
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            #we have already cleaned DB refs; report warning but don't fail hard
            return jsonify({"success": False, "warning": f"Removed references but failed to delete to delete file: {str(e)}"}), 200
        
    return ("", 204) #no content on success
    # return jsonify({"success": True})


@app.route("/delete_outfit", methods=["DELETE"])
def delete_outfit():
    """
    DELETE /delete_outfit?outfit_id=<id>
    Removes the outfit and its outfit_items. Returns counts for verification.
    """
    raw = request.args.get("outfit_id", None)
    try:
        outfit_id = int(raw)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid outfit_id", "got": raw}), 400

    conn = get_conn()
    cur = conn.cursor()

    # Verify exists
    cur.execute("SELECT id FROM outfits WHERE id = ?", (outfit_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Outfit not found", "outfit_id": outfit_id}), 404

    # Delete join rows first
    cur.execute("DELETE FROM outfit_items WHERE outfit_id = ?", (outfit_id,))
    deleted_items = cur.rowcount  # number of join rows deleted

    # Delete the outfit row
    cur.execute("DELETE FROM outfits WHERE id = ?", (outfit_id,))
    deleted_outfits = cur.rowcount

    conn.commit()
    conn.close()

    # Return explicit result (200 OK) so the frontend can message & verify
    return jsonify({
        "success": True,
        "deleted": {
            "outfits": int(deleted_outfits),
            "outfit_items": int(deleted_items)
        },
        "outfit_id": outfit_id
    }), 200

if __name__ == "__main__":
    init_db()
    # Run Flask on port 5001 instead of 5000
    app.run(host="0.0.0.0", port=5001, debug=True)
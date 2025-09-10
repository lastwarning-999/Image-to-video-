# AI Video Builder Flask App
# Credit: @hardhackar007 (Telegram)

from flask import Flask, request, jsonify, send_from_directory
import requests, base64, os
from werkzeug.utils import secure_filename
from urllib.parse import urlparse

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB

# APIs
VIDEO_API = "https://sii3.moayman.top/api/veo3.php"
IMGBB_API_KEY = "dec35aeb8aec4d57ec2babf304623204"
IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"


# ---------------- Helpers ----------------
def upload_to_imgbb(file_storage):
    """Upload file to ImgBB and return public URL"""
    try:
        filename = secure_filename(file_storage.filename)
        file_bytes = file_storage.read()
        b64 = base64.b64encode(file_bytes).decode("utf-8")
        payload = {"key": IMGBB_API_KEY, "image": b64, "name": filename}
        r = requests.post(IMGBB_UPLOAD_URL, data=payload, timeout=30)
        j = r.json()
        if j.get("success"):
            return j["data"]["url"]
    except Exception:
        return None
    return None


def is_valid_url(url):
    try:
        p = urlparse(url)
        return bool(p.scheme and p.netloc)
    except:
        return False


# ---------------- Routes ----------------
@app.route("/")
def index():
    # Serve index.html directly from root directory
    return send_from_directory(".", "index.html")


@app.route("/generate", methods=["POST"])
def generate():
    module = request.form.get("module", "TEXT_TO_VIDEO").upper()
    description = request.form.get("description", "").strip()

    if not description:
        return jsonify({"status": "error", "message": "Missing description."}), 400

    if module == "TEXT_TO_VIDEO":
        try:
            r = requests.get(f"{VIDEO_API}?text={requests.utils.requote_uri(description)}", timeout=60)
            j = r.json()
            video_url = j.get("video") if isinstance(j, dict) else None
            if video_url:
                return jsonify({"status": "ok", "video_url": video_url})
            return jsonify({"status": "error", "message": "No video returned."}), 502
        except Exception as e:
            return jsonify({"status": "error", "message": f"Error: {e}"}), 500

    if module == "IMAGE_TO_VIDEO":
        image_url = request.form.get("image_url", "").strip()
        if not image_url and "image_file" in request.files:
            image_url = upload_to_imgbb(request.files["image_file"])
        if not image_url or not is_valid_url(image_url):
            return jsonify({"status": "error", "message": "Invalid image."}), 400

        try:
            payload = {"text": description, "link": image_url}
            r = requests.post(VIDEO_API, data=payload, timeout=90)
            j = r.json()
            video_url = j.get("video") if isinstance(j, dict) else None
            if video_url:
                return jsonify({"status": "ok", "video_url": video_url})
            return jsonify({"status": "error", "message": "No video returned."}), 502
        except Exception as e:
            return jsonify({"status": "error", "message": f"Error: {e}"}), 500

    return jsonify({"status": "error", "message": "Unknown module"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

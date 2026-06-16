"""
Finance Dashboard - Cloud Server
Proxies Yahoo Finance API and serves the dashboard.
"""
import io
import json
import urllib.request
import urllib.parse
from flask import Flask, jsonify, request, send_from_directory
import fitz  # pymupdf
from docx import Document

app = Flask(__name__, static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/yahoo")
def proxy_yahoo():
    symbol = request.args.get("symbol", "")
    range_ = request.args.get("range", "5d")

    if not symbol:
        return jsonify({"error": "Missing symbol"}), 400

    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{urllib.parse.quote(symbol)}"
        f"?range={range_}&interval=1d&includePrePost=false"
    )

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()

        response = app.response_class(
            response=data,
            status=200,
            mimetype="application/json",
        )
        response.headers["Cache-Control"] = "public, max-age=300"
        return response

    except urllib.error.HTTPError as e:
        return jsonify({"error": f"Yahoo Finance: {e.code}"}), e.code
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.route("/api/extract-text", methods=["POST"])
def extract_text():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = file.filename.lower()

    try:
        if filename.endswith(".pdf"):
            data = file.read()
            doc = fitz.open(stream=data, filetype="pdf")
            pages = []
            for page in doc:
                text = page.get_text()
                if text:
                    pages.append(text)
            num_pages = len(doc)
            doc.close()
            full_text = "\n".join(pages)
            cjk_count = sum(1 for c in full_text if '一' <= c <= '鿿')
            garbled = len(full_text) > 100 and cjk_count < 5
            if garbled:
                return jsonify({
                    "text": "",
                    "pages": num_pages,
                    "note": "PDF 已上傳成功（此 PDF 使用特殊字型編碼，文字預覽不可用，但不影響後續處理）"
                })
            return jsonify({"text": full_text, "pages": num_pages})

        elif filename.endswith(".docx"):
            doc = Document(io.BytesIO(file.read()))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return jsonify({"text": "\n".join(paragraphs)})

        elif filename.endswith(".txt"):
            text = file.read().decode("utf-8", errors="replace")
            return jsonify({"text": text})

        else:
            return jsonify({"error": "Unsupported format"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

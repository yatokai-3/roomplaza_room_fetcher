from flask import Flask, request, jsonify
import automate_rp

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ok", "message": "the basic sh*t is working, less gooo ~ ~ ~ ~"})


@app.route("/rp", methods=["POST"])
def run():
    result = automate_rp.run_once()
    return jsonify(result)

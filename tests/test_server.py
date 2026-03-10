"""
Simple webhook server for testing.
Run this in one terminal, then run test_webhook_client.py in another.
"""

import os
import hmac
import hashlib
import json
import logging
from pathlib import Path
from flask import Flask, request, jsonify

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from file and environment variables."""
    config = {
        "port": 8080,
        "host": "0.0.0.0",
        "secret": "test-webhook-secret",
    }
    
    # Load from .env file (in parent directory)
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key, value)
    
    # Load from config file (in tests directory)
    config_file = Path(__file__).parent / "test-automation.config.json"
    if config_file.exists():
        with open(config_file) as f:
            file_config = json.load(f)
            webhook_config = file_config.get("webhook", {})
            config["port"] = webhook_config.get("port", config["port"])
            config["host"] = webhook_config.get("host", config["host"])
            config["secret"] = webhook_config.get("secret", config["secret"])
    
    # Environment variables override
    config["port"] = int(os.environ.get("WEBHOOK_PORT", config["port"]))
    config["host"] = os.environ.get("WEBHOOK_HOST", config["host"])
    config["secret"] = os.environ.get("GITHUB_WEBHOOK_SECRET", config["secret"])
    
    return config


CONFIG = load_config()
WEBHOOK_SECRET = CONFIG["secret"]
PORT = CONFIG["port"]
HOST = CONFIG["host"]

app = Flask(__name__)


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature."""
    if not signature or not secret:
        return False
    if not signature.startswith("sha256="):
        return False
    expected = signature[7:]
    computed = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(computed, expected)


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    logger.info("Health check requested")
    return jsonify({"status": "healthy", "service": "ai-harness-webhook-test"})


@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook endpoint."""
    event_type = request.headers.get("X-GitHub-Event", "")
    signature = request.headers.get("X-Hub-Signature-256", "")
    
    logger.info(f"=" * 50)
    logger.info(f"Received webhook: {event_type}")

    # Verify signature
    if not verify_signature(request.data, signature, WEBHOOK_SECRET):
        logger.warning("Invalid signature!")
        return jsonify({"error": "Invalid signature"}), 401

    try:
        payload = request.get_json()
    except Exception as e:
        return jsonify({"error": "Invalid JSON"}), 400

    action = payload.get("action", "")
    issue = payload.get("issue", {})
    repository = payload.get("repository", {})

    logger.info(f"Repository: {repository.get('full_name', 'unknown')}")
    logger.info(f"Action: {action}")
    
    if event_type == "issues" and issue:
        logger.info(f"Issue #{issue.get('number')}: {issue.get('title')}")
        logger.info(f"Labels: {[l.get('name') for l in issue.get('labels', [])]}")
        logger.info(f"Body preview: {issue.get('body', '')[:100]}...")

    logger.info("=" * 50)

    return jsonify({
        "message": "Webhook received successfully!",
        "event": event_type,
        "action": action,
        "issue_number": issue.get("number") if issue else None,
    })


if __name__ == "__main__":
    print("=" * 50)
    print("AI Harness Webhook Test Server")
    print("=" * 50)
    print(f"Server: http://{HOST}:{PORT}")
    print(f"Health: http://{HOST}:{PORT}/health")
    print(f"Webhook: http://{HOST}:{PORT}/webhook")
    print(f"Secret: {WEBHOOK_SECRET}")
    print("=" * 50)
    print("Press Ctrl+C to stop")
    print()
    
    app.run(host=HOST, port=PORT, debug=False)

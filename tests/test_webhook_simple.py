"""
Simple webhook server test without requiring GitHub Token.

This script tests only the webhook receiving functionality.
"""

import hmac
import hashlib
import json
import logging
import threading
import time
import sys
from flask import Flask, request, jsonify

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Test configuration
WEBHOOK_SECRET = "test-webhook-secret"
PORT = 8080

# Create Flask app
app = Flask(__name__)

# Store received webhooks
received_webhooks = []


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
    return jsonify({"status": "healthy", "service": "ai-harness-webhook-test"})


@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook endpoint."""
    # Get headers
    event_type = request.headers.get("X-GitHub-Event", "")
    signature = request.headers.get("X-Hub-Signature-256", "")
    delivery_id = request.headers.get("X-GitHub-Delivery", "")

    logger.info(f"Received webhook: {event_type} (delivery: {delivery_id})")

    # Verify signature
    if not verify_signature(request.data, signature, WEBHOOK_SECRET):
        logger.warning("Invalid signature!")
        return jsonify({"error": "Invalid signature"}), 401

    # Parse payload
    try:
        payload = request.get_json()
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}")
        return jsonify({"error": "Invalid JSON"}), 400

    # Log received data
    action = payload.get("action", "")
    issue = payload.get("issue", {})
    repository = payload.get("repository", {})

    logger.info(f"  Repository: {repository.get('full_name', 'unknown')}")
    logger.info(f"  Action: {action}")

    if event_type == "issues" and issue:
        logger.info(f"  Issue #{issue.get('number')}: {issue.get('title')}")
        logger.info(f"  Labels: {[l.get('name') for l in issue.get('labels', [])]}")

    # Store webhook
    received_webhooks.append({
        "event_type": event_type,
        "action": action,
        "repository": repository.get("full_name"),
        "issue_number": issue.get("number") if issue else None,
        "timestamp": time.time(),
    })

    return jsonify({
        "message": "Webhook received successfully",
        "event": event_type,
        "action": action,
    })


def send_test_webhook():
    """Send a test webhook after server starts."""
    import http.client

    # Wait for server to start
    time.sleep(1)

    # Create test payload
    payload = {
        "action": "opened",
        "issue": {
            "number": 999,
            "title": "[TEST] Test issue from automation",
            "body": "This is a test issue to verify the automation pipeline.",
            "html_url": "https://github.com/ninesun666/ninesun-blog/issues/999",
            "state": "open",
            "labels": [
                {"name": "enhancement"},
                {"name": "test"}
            ],
        },
        "repository": {
            "id": 123456789,
            "name": "ninesun-blog",
            "full_name": "ninesun666/ninesun-blog",
            "html_url": "https://github.com/ninesun666/ninesun-blog",
        },
        "sender": {
            "login": "test-user",
        },
    }

    # Compute signature
    payload_bytes = json.dumps(payload).encode("utf-8")
    signature = hmac.new(
        key=WEBHOOK_SECRET.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
    signature = f"sha256={signature}"

    # Send request
    logger.info("\n" + "=" * 50)
    logger.info("Sending test webhook...")
    logger.info(f"  Repository: ninesun666/ninesun-blog")
    logger.info(f"  Issue: #999 - [TEST] Test issue from automation")

    conn = http.client.HTTPConnection("localhost", PORT)
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "issues",
        "X-Hub-Signature-256": signature,
        "X-GitHub-Delivery": "test-delivery-123",
    }

    conn.request("POST", "/webhook", body=payload_bytes, headers=headers)
    response = conn.getresponse()
    body = response.read().decode("utf-8")

    logger.info(f"\nResponse: {response.status}")
    logger.info(f"Body: {body}")
    conn.close()

    # Print summary
    logger.info("\n" + "=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Webhooks received: {len(received_webhooks)}")
    if received_webhooks:
        for wh in received_webhooks:
            logger.info(f"  - {wh['event_type']}/{wh['action']} on {wh['repository']}")
    logger.info("\n✓ Webhook server test completed!")
    logger.info("=" * 50)

    # Shutdown server
    shutdown = request.environ.get("werkzeug.server.shutdown")
    if shutdown:
        shutdown()


def run_server():
    """Run the Flask server."""
    logger.info("=" * 50)
    logger.info("AI Harness Webhook Test Server")
    logger.info("=" * 50)
    logger.info(f"Starting server on http://localhost:{PORT}")
    logger.info(f"Webhook endpoint: /webhook")
    logger.info(f"Secret: {WEBHOOK_SECRET}")
    logger.info("=" * 50 + "\n")

    # Start test webhook sender in background
    test_thread = threading.Thread(target=send_test_webhook, daemon=True)
    test_thread.start()

    # Run Flask app
    app.run(host="0.0.0.0", port=PORT, debug=False)


if __name__ == "__main__":
    run_server()

"""
Test script to simulate GitHub webhook calls.

This script sends a simulated webhook request to the local
automation server for testing purposes.
"""

import hmac
import hashlib
import json
import http.client
import sys
from datetime import datetime


def compute_signature(payload: bytes, secret: str) -> str:
    """Compute GitHub webhook signature."""
    signature = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return f"sha256={signature}"


def create_issue_payload(
    repo_owner: str,
    repo_name: str,
    issue_number: int,
    issue_title: str,
    issue_body: str,
    labels: list = None,
):
    """Create a simulated GitHub issue webhook payload."""
    return {
        "action": "opened",
        "issue": {
            "number": issue_number,
            "title": issue_title,
            "body": issue_body,
            "html_url": f"https://github.com/{repo_owner}/{repo_name}/issues/{issue_number}",
            "state": "open",
            "labels": [{"name": label} for label in (labels or [])],
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
        },
        "repository": {
            "id": 123456789,
            "name": repo_name,
            "full_name": f"{repo_owner}/{repo_name}",
            "html_url": f"https://github.com/{repo_owner}/{repo_name}",
            "clone_url": f"https://github.com/{repo_owner}/{repo_name}.git",
        },
        "sender": {
            "login": "test-user",
            "id": 12345,
        },
    }


def send_webhook(
    payload: dict,
    secret: str,
    host: str = "localhost",
    port: int = 8080,
    path: str = "/webhook",
):
    """Send a webhook request to the server."""
    payload_bytes = json.dumps(payload).encode("utf-8")
    signature = compute_signature(payload_bytes, secret)

    conn = http.client.HTTPConnection(host, port)
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "issues",
        "X-Hub-Signature-256": signature,
        "X-GitHub-Delivery": "test-delivery-123",
    }

    print(f"Sending webhook to http://{host}:{port}{path}")
    print(f"Event: issues")
    print(f"Signature: {signature[:20]}...")

    conn.request("POST", path, body=payload_bytes, headers=headers)
    response = conn.getresponse()

    print(f"\nResponse Status: {response.status}")
    print(f"Response Headers: {dict(response.getheaders())}")

    body = response.read().decode("utf-8")
    print(f"Response Body: {body}")

    conn.close()
    return response.status, body


def test_health_check(host: str = "localhost", port: int = 8080):
    """Test the health check endpoint."""
    conn = http.client.HTTPConnection(host, port)
    conn.request("GET", "/health")
    response = conn.getresponse()
    body = response.read().decode("utf-8")
    print(f"Health Check: {response.status} - {body}")
    conn.close()
    return response.status == 200


def main():
    # Configuration
    SECRET = "test-webhook-secret"
    HOST = "localhost"
    PORT = 8080

    # Test repository
    REPO_OWNER = "ninesun666"
    REPO_NAME = "ninesun-blog"

    print("=" * 60)
    print("AI Harness Webhook Test")
    print("=" * 60)

    # First, test health check
    print("\n1. Testing health check...")
    if not test_health_check(HOST, PORT):
        print("ERROR: Server is not running or health check failed!")
        print("Please start the server first:")
        print("  python -m issue_automator.cli automation start -c test-automation.config.json")
        sys.exit(1)

    print("\n2. Sending test issue webhook...")

    # Create test issue payload
    payload = create_issue_payload(
        repo_owner=REPO_OWNER,
        repo_name=REPO_NAME,
        issue_number=999,
        issue_title="[TEST] Automated test issue",
        issue_body="""## Description

This is a test issue to verify the automation pipeline.

## Acceptance Criteria

- [ ] Webhook receives the event
- [ ] Pipeline processes the issue
- [ ] Notification is sent

## Technical Notes

- This is a simulated test
- No actual code changes will be made
""",
        labels=["test", "enhancement"],
    )

    print(f"\nIssue #{payload['issue']['number']}: {payload['issue']['title']}")
    print(f"Repository: {payload['repository']['full_name']}")

    # Send webhook
    status, body = send_webhook(payload, SECRET, HOST, PORT)

    if status == 200:
        print("\n✓ Webhook test successful!")
    else:
        print(f"\n✗ Webhook test failed with status {status}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

"""
Webhook client test script.
Run this after starting test_server.py.
"""

import os
import hmac
import hashlib
import json
import http.client
from pathlib import Path


def load_config():
    """Load configuration from file and environment variables."""
    config = {
        "port": 8080,
        "host": "localhost",
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
            config["secret"] = webhook_config.get("secret", config["secret"])
    
    # Environment variables override
    config["port"] = int(os.environ.get("WEBHOOK_PORT", config["port"]))
    config["secret"] = os.environ.get("GITHUB_WEBHOOK_SECRET", config["secret"])
    
    return config


def send_test_webhook():
    """Send a test webhook to the local server."""
    config = load_config()
    SECRET = config["secret"]
    HOST = config["host"]
    PORT = config["port"]
    
    # Test payload for ninesun666/ninesun-blog
    payload = {
        "action": "opened",
        "issue": {
            "number": 999,
            "title": "[TEST] Add dark mode support",
            "body": """## Description

Add dark mode support to the blog application.

## Acceptance Criteria

- [ ] Add dark mode toggle in header
- [ ] Persist preference in localStorage
- [ ] Apply dark theme to all pages

## Technical Notes

- Use CSS custom properties for theming
- Consider system preference detection
""",
            "html_url": "https://github.com/ninesun666/ninesun-blog/issues/999",
            "state": "open",
            "labels": [
                {"name": "enhancement"},
                {"name": "feature"}
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
        key=SECRET.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
    signature = f"sha256={signature}"
    
    # Send request
    print("=" * 50)
    print("Sending Test Webhook")
    print("=" * 50)
    print(f"Repository: ninesun666/ninesun-blog")
    print(f"Issue: #999 - Add dark mode support")
    print(f"Labels: enhancement, feature")
    print()
    
    conn = http.client.HTTPConnection(HOST, PORT)
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "issues",
        "X-Hub-Signature-256": signature,
        "X-GitHub-Delivery": "test-delivery-001",
    }
    
    try:
        conn.request("POST", "/webhook", body=payload_bytes, headers=headers)
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        
        print(f"Response Status: {response.status}")
        print(f"Response Body: {body}")
        
        if response.status == 200:
            print()
            print("✓ Webhook test successful!")
        else:
            print()
            print(f"✗ Webhook test failed!")
            
    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Make sure the server is running:")
        print("  python test_server.py")
    finally:
        conn.close()
    
    print("=" * 50)


if __name__ == "__main__":
    send_test_webhook()

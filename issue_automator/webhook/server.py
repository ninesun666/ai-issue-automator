"""
Flask-based webhook server for GitHub events.

This module provides a webhook server that receives GitHub webhook
events and dispatches them to the automation pipeline.
"""

import json
import logging
from typing import Any, Callable, Dict, Optional

from flask import Flask, Request, request, jsonify

from issue_automator.webhook.handlers import GitHubEventHandler, WebhookResult
from issue_automator.webhook.signature import verify_github_signature

logger = logging.getLogger(__name__)


class WebhookServer:
    """
    Flask-based webhook server for GitHub events.

    This server listens for GitHub webhook events and processes
    them through the automation pipeline.

    Example:
        >>> server = WebhookServer(secret="my-secret", port=8080)
        >>> server.on_issue_created(my_handler)
        >>> server.start()
    """

    def __init__(
        self,
        secret: str,
        host: str = "0.0.0.0",
        port: int = 8080,
        path: str = "/webhook",
        debug: bool = False,
    ):
        """
        Initialize the webhook server.

        Args:
            secret: GitHub webhook secret for signature verification
            host: Host address to bind to
            port: Port number to listen on
            path: URL path for the webhook endpoint
            debug: Enable Flask debug mode
        """
        self.secret = secret
        self.host = host
        self.port = port
        self.path = path
        self.debug = debug

        self._app = Flask(__name__)
        self._handler = GitHubEventHandler()
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Set up Flask routes."""
        self._app.add_url_rule(
            self.path,
            endpoint="webhook",
            view_func=self._handle_webhook,
            methods=["POST"],
        )

        self._app.add_url_rule(
            "/health",
            endpoint="health",
            view_func=self._health_check,
            methods=["GET"],
        )

    def _health_check(self):
        """Health check endpoint."""
        return jsonify({"status": "healthy", "service": "ai-harness-webhook"})

    def _handle_webhook(self):
        """
        Handle incoming webhook requests.

        This method verifies the signature, parses the payload,
        and dispatches to the appropriate handler.
        """
        # Get event type from header
        event_type = request.headers.get("X-GitHub-Event", "")
        if not event_type:
            logger.warning("Missing X-GitHub-Event header")
            return jsonify({"error": "Missing event type"}), 400

        # Verify signature
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not verify_github_signature(request.data, signature, self.secret):
            logger.warning("Invalid webhook signature")
            return jsonify({"error": "Invalid signature"}), 401

        # Parse payload
        try:
            payload = request.get_json()
            if payload is None:
                return jsonify({"error": "Invalid JSON payload"}), 400
        except Exception as e:
            logger.error(f"Failed to parse JSON: {e}")
            return jsonify({"error": "Invalid JSON"}), 400

        # Get action if present
        action = payload.get("action")

        # Handle the event
        result = self._handler.handle_event(event_type, action, payload)

        if result.success:
            return jsonify({
                "message": result.message,
                "data": result.data,
            }), 200
        else:
            return jsonify({
                "error": result.error or result.message,
            }), 500

    def on_issue_created(
        self,
        callback: Callable[[Any], None],
    ) -> None:
        """
        Register callback for issue created events.

        Args:
            callback: Function to call when an issue is created
        """
        self._handler._callbacks["opened"] = callback

    def on_issue_closed(
        self,
        callback: Callable[[Any], None],
    ) -> None:
        """
        Register callback for issue closed events.

        Args:
            callback: Function to call when an issue is closed
        """
        self._handler._callbacks["closed"] = callback

    def on_issue_labeled(
        self,
        callback: Callable[[Any], None],
    ) -> None:
        """
        Register callback for issue labeled events.

        Args:
            callback: Function to call when an issue is labeled
        """
        self._handler._callbacks["labeled"] = callback

    def start(self) -> None:
        """Start the webhook server."""
        logger.info(f"Starting webhook server on {self.host}:{self.port}")
        logger.info(f"Webhook endpoint: {self.path}")
        self._app.run(
            host=self.host,
            port=self.port,
            debug=self.debug,
        )

    def get_app(self) -> Flask:
        """Get the Flask application instance for testing."""
        return self._app

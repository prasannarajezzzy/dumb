import os
import logging
from quart import Quart, request, jsonify
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.signature import SignatureVerifier
from dotenv import load_dotenv
from pathlib import Path
from llm import get_llm_response
import asyncio

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Quart app
app = Quart(__name__)

# Slack client and signature verifier
slack_client = AsyncWebClient(token=os.getenv('SLACK_TOKEN'))
signature_verifier = SignatureVerifier(os.getenv('SLACK_SIGNING_SECRET'))

try:
    BOT_ID = asyncio.run(slack_client.auth_test())["user_id"]
except Exception as e:
    logger.error(f"Error retrieving BOT ID: {e}")
    raise

@app.route('/slack/events', methods=['POST'])
async def slack_events():
    """Endpoint for handling Slack events."""
    try:
        # Verify the request signature
        if not signature_verifier.is_valid_request(await request.get_data(), request.headers):
            return "Invalid request signature", 403

        payload = await request.json
        logger.info(f"Received payload: {payload}")

        if "challenge" in payload:
            return jsonify({"challenge": payload["challenge"]})

        event = payload.get("event", {})
        if event.get("type") == "message" and not event.get("bot_id"):
            channel_id = event.get("channel")
            user_id = event.get("user")
            text = event.get("text")

            if BOT_ID != user_id:
                logger.info(f"Received message: {text} from user: {user_id}")
                
                # Use asyncio.create_task to parallelize processing
                response_task = asyncio.create_task(get_llm_response(text))
                response = await response_task
                
                await slack_client.chat_postMessage(channel=channel_id, text=response)
                logger.info(f"LLM Response sent: {response}")

        return jsonify({"status": "ok"})

    except Exception as e:
        logger.error(f"Error processing Slack event: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
async def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

    logger.info(f"Starting Quart app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)

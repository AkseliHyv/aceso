import json
import time

def publish_and_wait(mqtt, topic, payload, attempts=5, delay=1):
    """Publish MQTT message and wait for response."""
    mqtt["last_message"] = None
    mqtt["client"].publish(topic, json.dumps(payload))
    wait_for_response(mqtt, attempts, delay)
    return json.loads(mqtt["last_message"])

def wait_for_response(mqtt, attempts, delay):
    """Poll for MQTT message with retries."""
    for _ in range(attempts):
        mqtt["client"].check_msg()
        if mqtt["last_message"]:
            return True
        time.sleep(delay)
    return False

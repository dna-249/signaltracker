import logging
import requests
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("NOCNotifier")

class NOCNotifier:
    def __init__(self, webhook_url: str = None):
        """
        Initializes the notification dispatcher for the Network Operations Center (NOC).
        """
        self.webhook_url = webhook_url

    def send_interference_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Sends an immediate high-priority alert payload via Webhook to the NOC operator dashboard 
        or messaging channel.
        """
        transponder_id = alert_data.get("transponder_id")
        trigger = alert_data.get("trigger_source")
        metrics = alert_data.get("metrics", {})

        message = {
            "content": f"🚨 **CRITICAL BEAM INTERFERENCE DETECTED** 🚨",
            "embeds": [
                {
                    "title": f"Transponder: {transponder_id}",
                    "color": 15548997,  # Red alert indicator color code
                    "fields": [
                        {"name": "Trigger Engine", "value": str(trigger), "inline": True},
                        {"name": "Power Delta", "value": f"{metrics.get('power_delta_db', 0)} dB", "inline": True},
                        {"name": "SNR Drop", "value": f"{metrics.get('snr_drop_db', 0)} dB", "inline": True},
                        {"name": "Frequency Drift", "value": f"{metrics.get('frequency_drift_hz', 0)} Hz", "inline": True}
                    ]
                }
            ]
        }

        logger.warning(f"Dispatching emergency incident notification for {transponder_id}...")

        # If no external webhook is registered, run in simulated console notification mode
        if not self.webhook_url:
            logger.info(f"[SIMULATED NOC NOTIFICATION]: Transponder {transponder_id} compromised! Trigger: {trigger}")
            return True

        try:
            response = requests.post(self.webhook_url, json=message, timeout=5)
            if response.status_code in [200, 204]:
                logger.info(f"NOC Alert successfully dispatched via webhook for {transponder_id}")
                return True
            else:
                logger.error(f"Failed to deliver webhook notification. Status code: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Network error while sending NOC alert: {e}")
            return False

if __name__ == "__main__":
    # Standalone test stub
    notifier = NOCNotifier()
    sample_alert = {
        "transponder_id": "NIGCOMSAT-1R-TP1",
        "timestamp": 1711900000.0,
        "trigger_source": "RULE_ENGINE",
        "metrics": {
            "power_delta_db": 7.5,
            "snr_drop_db": 14.0,
            "frequency_drift_hz": 2200.0
        }
    }
    notifier.send_interference_alert(sample_alert)
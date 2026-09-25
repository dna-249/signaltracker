import json
import logging
from kafka import KafkaConsumer
from typing import Callable, Dict, Any

# Configure logging for the network operations stream
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("StreamConsumer")

class SatelliteStreamConsumer:
    def __init__(self, topic: str, bootstrap_servers: list[str], process_callback: Callable[[Dict[Any, Any]], None]):
        """
        Initializes the Kafka stream consumer for satellite telemetry.
        """
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.process_callback = process_callback
        
        logger.info(f"Initializing Consumer for topic '{self.topic}' targeting servers {self.bootstrap_servers}")
        
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='nigcomsat-noc-monitor-group',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
        except Exception as e:
            logger.warning(f"Kafka broker connection failed: {e}. Falling back to simulation mode handler.")
            self.consumer = None

    def start_consuming(self):
        """
        Continuously polls the message stream for real-time telemetry packets.
        """
        if not self.consumer:
            logger.error("No active message broker connection available to consume streams.")
            return

        logger.info("Stream consumer active. Listening for live transponder telemetry frames...")
        try:
            for message in self.consumer:
                telemetry_payload = message.value
                logger.debug(f"Received payload from partition {message.partition}: {telemetry_payload}")
                
                # Pass data payload to detection processor callback
                self.process_callback(telemetry_payload)
                
        except KeyboardInterrupt:
            logger.info("Stream consumption manually halted by operator.")
        finally:
            if self.consumer:
                self.consumer.close()

if __name__ == "__main__":
    # Test stub callback
    def dummy_processor(data):
        print("Processed Telemetry Packet:", data.get("transponder_id"))

    # Example instantiation
    stream_listener = SatelliteStreamConsumer(
        topic="satellite-telemetry-feed",
        bootstrap_servers=["localhost:9092"],
        process_callback=dummy_processor
    )
    # stream_listener.start_consuming()
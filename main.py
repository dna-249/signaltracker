import time
import logging
from src.ingestion import SatelliteTelemetrySimulator
from src.processing import BeamIntegrityDetector
from src.storage import TelemetryDatabase
from src.alerts import NOCNotifier

# Configure master logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("NIGCOMSAT-MainOrchestrator")

def run_pipeline(interval_seconds: float = 2.0, anomaly_chance: float = 0.3):
    """
    Orchestrates the continuous real-time satellite beam integrity monitoring pipeline.
    """
    logger.info("Initializing NIGCOMSAT Beam Integrity Monitoring Pipeline...")
    
    # Initialize core modules
    simulator = SatelliteTelemetrySimulator(baseline_path="data/historical_baselines.json")
    detector = BeamIntegrityDetector(baseline_path="data/historical_baselines.json")
    db = TelemetryDatabase(db_path="data/telemetry.db")
    notifier = NOCNotifier(webhook_url=None) # Uses simulated console logging if no webhook is provided

    logger.info("Pipeline components ready. Starting live telemetry ingestion loop...")
    logger.info("Press Ctrl+C to halt execution.")

    try:
        while True:
            # 1. Generate a batch of simulated telemetry frames for all transponders
            telemetry_batch = simulator.generate_frame(inject_anomaly=(random_chance() < anomaly_chance))
            
            for frame in telemetry_batch:
                # 2. Persist raw telemetry packet to local timeseries DB
                db.insert_telemetry(frame)

                # 3. Evaluate frame through the rule-based and ML anomaly detector
                assessment = detector.evaluate_telemetry(frame)

                # 4. Handle compromised beam events
                if assessment.get("anomaly_detected"):
                    db.insert_alert(assessment)
                    notifier.send_interference_alert(assessment)
                else:
                    logger.info(f"🟢 Nominal: {frame['transponder_id']} | Power: {frame['carrier_power_dbm']} dBm | SNR: {frame['snr_db']} dB")

            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        logger.info("Monitoring pipeline manually halted by operator.")

def random_chance():
    import random
    return random.random()

if __name__ == "__main__":
    run_pipeline(interval_seconds=3.0, anomaly_chance=0.25)
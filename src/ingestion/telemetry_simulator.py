import json
import time
import random
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("TelemetrySimulator")

class SatelliteTelemetrySimulator:
    def __init__(self, baseline_path: str = "data/historical_baselines.json"):
        """
        Initializes the simulator by loading historical baselines for NIGCOMSAT transponders.
        """
        self.baseline_path = Path(baseline_path)
        self.transponders = self._load_baselines()

    def _load_baselines(self) -> list:
        if not self.baseline_path.exists():
            logger.error(f"Baseline configuration file not found at {self.baseline_path}")
            return []
        
        with open(self.baseline_path, "r") as f:
            data = json.load(f)
            return data.get("transponders", [])

    def generate_frame(self, inject_anomaly: bool = False) -> list[dict]:
        """
        Generates a live telemetry batch for all active transponders.
        Optionally injects a severe interference anomaly into a randomly chosen transponder.
        """
        if not self.transponders:
            logger.warning("No transponder configurations available to simulate.")
            return []

        frames = []
        anomaly_target = random.choice(self.transponders)["id"] if inject_anomaly else None

        for tp in self.transponders:
            tp_id = tp["id"]
            
            # Normal environmental signal jitter
            power_jitter = random.uniform(-0.4, 0.4)
            snr_jitter = random.uniform(-0.2, 0.2)
            freq_drift = random.uniform(-50.0, 50.0)

            carrier_power = tp["baseline_carrier_power_dbm"] + power_jitter
            noise_power = tp["baseline_noise_power_dbm"] + random.uniform(-0.1, 0.1)
            snr = tp["baseline_snr_db"] + snr_jitter
            frequency = (tp["frequency_ghz"] * 1e9) + freq_drift # Frequency in Hertz

            # Inject artificial interference if targeted
            is_anomaly = (tp_id == anomaly_target)
            if is_anomaly:
                logger.warning(f"INTERFERENCE DETECTED / INJECTED on transponder: {tp_id}")
                carrier_power += 7.5   # Abnormal surge in carrier power due to interference/jamming
                snr -= 14.0            # Severe degradation in Signal-to-Noise Ratio
                freq_drift += 2200.0   # Frequency drift exceeding acceptable limits

            payload = {
                "timestamp": time.time(),
                "transponder_id": tp_id,
                "frequency_hz": frequency,
                "polarization": tp["polarization"],
                "carrier_power_dbm": round(carrier_power, 2),
                "noise_power_dbm": round(noise_power, 2),
                "snr_db": round(snr, 2),
                "frequency_drift_hz": round(freq_drift, 2),
                "is_simulated_anomaly": is_anomaly
            }
            frames.append(payload)

        return frames

    def stream_continuously(self, interval_seconds: float = 2.0, anomaly_chance: float = 0.25):
        """
        Continuously yields telemetry frames in real-time intervals.
        """
        logger.info(f"Starting satellite telemetry simulation stream (Interval: {interval_seconds}s)...")
        try: 
            while True:
                # Decide whether to inject an anomaly based on the probability chance
                inject = random.random() < anomaly_chance
                batch = self.generate_frame(inject_anomaly=inject)
                
                for frame in batch:
                    status = "⚠️ ANOMALY" if frame["is_simulated_anomaly"] else "✅ NORMAL"
                    logger.info(f"[{status}] Transponder: {frame['transponder_id']} | Power: {frame['carrier_power_dbm']} dBm | SNR: {frame['snr_db']} dB")
                
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("Telemetry simulation stream manually halted.")

if __name__ == "__main__":
    simulator = SatelliteTelemetrySimulator()
    simulator.stream_continuously(interval_seconds=3.0, anomaly_chance=0.3)
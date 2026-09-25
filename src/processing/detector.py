import json
import logging
import numpy as np
from pathlib import Path
from sklearn.ensemble import IsolationForest
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("BeamIntegrityDetector")

class BeamIntegrityDetector:
    def __init__(self, baseline_path: str = "data/historical_baselines.json"):
        """
        Initializes the detector with historical baselines and configures an Isolation Forest model.
        """
        self.baseline_path = Path(baseline_path)
        self.baselines = self._load_baselines()
        
        # Initialize an unsupervised Isolation Forest model for multi-dimensional telemetry anomaly detection
        self.model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
        self._is_fitted = False
        self._initialize_baseline_model()

    def _load_baselines(self) -> Dict[str, Dict[str, Any]]:
        if not self.baseline_path.exists():
            logger.error(f"Baseline file missing at {self.baseline_path}")
            return {}
        
        with open(self.baseline_path, "r") as f:
            data = json.load(f)
            # Map transponder ID to its profile for fast $O(1)$ lookup
            return {tp["id"]: tp for tp in data.get("transponders", [])}

    def _initialize_baseline_model(self):
        """
        Pre-trains/fits the Isolation Forest model using synthetic nominal data generated from baselines.
        """
        training_samples = []
        for tp_id, profile in self.baselines.items():
            # Generate nominal training points based on baseline behavior
            for _ in range(50):
                p_noise = np.random.normal(0, 0.2)
                s_noise = np.random.normal(0, 0.1)
                f_noise = np.random.normal(0, 20.0)
                
                training_samples.append([
                    profile["baseline_carrier_power_dbm"] + p_noise,
                    profile["baseline_snr_db"] + s_noise,
                    f_noise
                ])
        
        if training_samples:
            X_train = np.array(training_samples)
            self.model.fit(X_train)
            self._is_fitted = True
            logger.info("Isolation Forest anomaly detector successfully fitted on nominal transponder baselines.")

    def evaluate_telemetry(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a single incoming telemetry packet using threshold limits and Machine Learning.
        """
        tp_id = payload.get("transponder_id")
        carrier_power = payload.get("carrier_power_dbm")
        snr = payload.get("snr_db")
        freq_drift = payload.get("frequency_drift_hz", 0.0)

        profile = self.baselines.get(tp_id)
        if not profile:
            logger.warning(f"Unknown transponder ID received: {tp_id}")
            return {"status": "UNKNOWN", "anomaly_detected": False}

        # 1. Rule-Based Threshold Check
        allowed = profile["allowed_variance"]
        power_delta = abs(carrier_power - profile["baseline_carrier_power_dbm"])
        snr_drop = profile["baseline_snr_db"] - snr

        rule_anomaly = (
            power_delta > allowed["power_delta_max"] or
            snr_drop > allowed["snr_drop_max"] or
            abs(freq_drift) > allowed["frequency_drift_hz_max"]
        )

        # 2. Machine Learning Model Check (Isolation Forest)
        ml_anomaly = False
        if self._is_fitted:
            X_test = np.array([[carrier_power, snr, freq_drift]])
            prediction = self.model.predict(X_test)  # Returns -1 for anomaly, 1 for inlier
            ml_anomaly = (prediction[0] == -1)

        # Final verdict combines strict domain rules with ML insight
        is_compromised = rule_anomaly or ml_anomaly

        result = {
            "transponder_id": tp_id,
            "timestamp": payload.get("timestamp"),
            "anomaly_detected": is_compromised,
            "trigger_source": "RULE_ENGINE" if rule_anomaly else ("ML_MODEL" if ml_anomaly else None),
            "metrics": {
                "power_delta_db": round(power_delta, 2),
                "snr_drop_db": round(snr_drop, 2),
                "frequency_drift_hz": freq_drift
            }
        }

        if is_compromised:
            logger.warning(f"⚠️ BEAM INTEGRITY COMPROMISED on {tp_id}! Trigger: {result['trigger_source']}")
        
        return result

if __name__ == "__main__":
    # Quick standalone test
    detector = BeamIntegrityDetector()
    sample_packet = {
        "timestamp": 1711900000.0,
        "transponder_id": "NIGCOMSAT-1R-TP1",
        "carrier_power_dbm": -58.0,  # Spiked power
        "snr_db": 18.5,             # Dropped SNR
        "frequency_drift_hz": 2500.0
    }
    assessment = detector.evaluate_telemetry(sample_packet)
    print(json.dumps(assessment, indent=2))
import logging
import numpy as np
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("BeamMetricsCalculator")

class BeamMetricsCalculator:
    @staticmethod
    def calculate_cnr(carrier_power_dbm: float, noise_power_dbm: float) -> float:
        """
        Calculates the Carrier-to-Noise Ratio (CNR) in decibels (dB).
        Formula: CNR = Carrier Power (dBm) - Noise Power (dBm)
        """
        try:
            cnr = carrier_power_dbm - noise_power_dbm
            return round(cnr, 2)
        except Exception as e:
            logger.error(f"Error calculating CNR: {e}")
            return 0.0

    @staticmethod
    def calculate_link_margin(current_cnr_db: float, required_threshold_db: float) -> float:
        """
        Calculates the operational link margin. 
        A positive margin indicates a healthy link; a negative margin means risk of signal outage.
        """
        margin = current_cnr_db - required_threshold_db
        return round(margin, 2)

    @staticmethod
    def compute_rolling_window_stats(telemetry_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Computes rolling statistics (mean and standard deviation) over a sliding window 
        of recent telemetry payloads for a specific transponder.
        """
        if not telemetry_history:
            return {"mean_carrier_power": 0.0, "std_carrier_power": 0.0, "mean_snr": 0.0, "std_snr": 0.0}

        powers = [entry.get("carrier_power_dbm", 0.0) for entry in telemetry_history]
        snrs = [entry.get("snr_db", 0.0) for entry in telemetry_history]

        stats = {
            "mean_carrier_power": round(float(np.mean(powers)), 2),
            "std_carrier_power": round(float(np.std(powers)), 2),
            "mean_snr": round(float(np.mean(snrs)), 2),
            "std_snr": round(float(np.std(snrs)), 2)
        }
        return stats

if __name__ == "__main__":
    # Quick standalone test
    calc = BeamMetricsCalculator()
    test_cnr = calc.calculate_cnr(-65.5, -98.0)
    test_margin = calc.calculate_link_margin(test_cnr, 25.0)
    print(f"Calculated CNR: {test_cnr} dB")
    print(f"Calculated Link Margin: {test_margin} dB")
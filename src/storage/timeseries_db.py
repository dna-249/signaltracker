import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("TelemetryDatabase")

class TelemetryDatabase:
    def __init__(self, db_path: str = "data/telemetry.db"):
        """
        Initializes the SQLite storage layer for telemetry logs and anomaly alerts.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries for convenience
        return conn

    def _initialize_database(self):
        """
        Creates necessary tables for raw telemetry and triggered anomaly incidents.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Table for continuous telemetry streams
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    transponder_id TEXT,
                    frequency_hz REAL,
                    polarization TEXT,
                    carrier_power_dbm REAL,
                    noise_power_dbm REAL,
                    snr_db REAL,
                    frequency_drift_hz REAL,
                    is_simulated_anomaly BOOLEAN
                )
            """)

            # Table for recorded interference / integrity breaches
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS anomaly_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    transponder_id TEXT,
                    trigger_source TEXT,
                    details TEXT
                )
            """)
            conn.commit()
            logger.info(f"Local timeseries SQLite database successfully initialized at {self.db_path}")

    def insert_telemetry(self, payload: Dict[str, Any]):
        """
        Inserts a single raw telemetry packet into the database.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO telemetry_logs (
                        timestamp, transponder_id, frequency_hz, polarization, 
                        carrier_power_dbm, noise_power_dbm, snr_db, frequency_drift_hz, is_simulated_anomaly
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    payload.get("timestamp"),
                    payload.get("transponder_id"),
                    payload.get("frequency_hz"),
                    payload.get("polarization"),
                    payload.get("carrier_power_dbm"),
                    payload.get("noise_power_dbm"),
                    payload.get("snr_db"),
                    payload.get("frequency_drift_hz"),
                    payload.get("is_simulated_anomaly", False)
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to insert telemetry log: {e}")

    def insert_alert(self, alert_data: Dict[str, Any]):
        """
        Logs a confirmed beam interference or integrity breach event.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO anomaly_alerts (timestamp, transponder_id, trigger_source, details)
                    VALUES (?, ?, ?, ?)
                """, (
                    alert_data.get("timestamp"),
                    alert_data.get("transponder_id"),
                    alert_data.get("trigger_source"),
                    json.dumps(alert_data.get("metrics", {}))
                ))
                conn.commit()
                logger.info(f"Anomaly alert logged in database for {alert_data.get('transponder_id')}")
        except Exception as e:
            logger.error(f"Failed to insert anomaly alert: {e}")

    def get_recent_logs(self, transponder_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieves recent telemetry records for dashboard trend rendering.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM telemetry_logs 
                WHERE transponder_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (transponder_id, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

if __name__ == "__main__":
    db = TelemetryDatabase()
    print("Database ready for persistence.")
import sqlite3
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="NIGCOMSAT Beam Integrity & Interference Monitor",
    description="Real-time operational dashboard for satellite transponder telemetry and anomaly detection.",
    version="1.0.0"
)

# Mount the static directory to serve CSS, JS, and assets
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

DB_PATH = Path("data/telemetry.db")

def get_db_connection():
    if not DB_PATH.exists():
        raise HTTPException(status_code=500, detail="Telemetry database not found. Run main.py first.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    """
    Serves a fully interactive, real-time NOC operations dashboard UI with live spectrum tracking.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NIGCOMSAT - Beam Integrity NOC Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body class="bg-slate-950 text-slate-100 font-sans min-h-screen">
        <header class="bg-slate-900 border-b border-slate-800 px-6 py-4 flex justify-between items-center">
            <div class="flex items-center space-x-3">
                <div class="h-3 w-3 bg-emerald-500 rounded-full animate-pulse"></div>
                <h1 class="text-xl font-bold tracking-wide">NIGCOMSAT <span class="text-indigo-400">NOC Monitor</span></h1>
            </div>
            <div class="text-sm text-slate-400">DNICE 2026 Showcase Prototype</div>
        </header>

        <main class="p-6 max-w-7xl mx-auto space-y-6">
            <!-- Metrics Summary Cards -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl">
                    <h3 class="text-slate-400 text-sm font-medium">Active Transponders</h3>
                    <p id="stat-transponders" class="text-3xl font-bold mt-2 text-indigo-400">3</p>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl">
                    <h3 class="text-slate-400 text-sm font-medium">System Status</h3>
                    <p id="stat-status" class="text-3xl font-bold mt-2 text-emerald-400">NOMINAL</p>
                </div>
                <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl">
                    <h3 class="text-slate-400 text-sm font-medium">Total Anomaly Alerts</h3>
                    <p id="stat-alerts" class="text-3xl font-bold mt-2 text-amber-400">0</p>
                </div>
            </div>

            <!-- Live RF Carrier Power & SNR Spectrum Chart Section -->
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <h2 class="text-lg font-semibold mb-4 text-slate-200">Live RF Carrier Power & SNR Spectrum</h2>
                <div class="relative h-72 w-full">
                    <canvas id="spectrumChart"></canvas>
                </div>
            </div>

            <!-- Live Telemetry Feed & Alerts Section -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Recent Telemetry Log Table -->
                <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 overflow-hidden">
                    <h2 class="text-lg font-semibold mb-4 text-slate-200">Live Telemetry Ingestion Stream</h2>
                    <div class="overflow-x-auto max-h-96 overflow-y-auto">
                        <table class="w-full text-left text-sm text-slate-300">
                            <thead class="bg-slate-800 text-slate-400 uppercase text-xs">
                                <tr>
                                    <th class="p-3">Transponder</th>
                                    <th class="p-3">Power (dBm)</th>
                                    <th class="p-3">SNR (dB)</th>
                                    <th class="p-3">Status</th>
                                </tr>
                            </thead>
                            <tbody id="telemetry-table-body" class="divide-y divide-slate-800">
                                <!-- Dynamic rows injected via JS -->
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Active Anomaly Incident Feed -->
                <div class="bg-slate-900 border border-slate-800 rounded-xl p-5">
                    <h2 class="text-lg font-semibold mb-4 text-slate-200">Interference & Breach Incident Log</h2>
                    <div id="alerts-container" class="space-y-3 max-h-96 overflow-y-auto pr-2">
                        <p class="text-slate-500 text-sm italic">No security breaches or jamming incidents recorded yet.</p>
                    </div>
                </div>
            </div>
        </main>

        <script>
            async function fetchData() {
                try {
                    const response = await fetch('/api/summary');
                    const data = await response.json();
                    
                    // Update Alert Count
                    document.getElementById('stat-alerts').innerText = data.total_alerts;
                    
                    // Render Telemetry Rows
                    const tbody = document.getElementById('telemetry-table-body');
                    tbody.innerHTML = '';
                    data.recent_telemetry.forEach(row => {
                        const tr = document.createElement('tr');
                        const statusBadge = row.is_simulated_anomaly 
                            ? '<span class="bg-red-950 text-red-400 px-2 py-1 rounded text-xs font-bold border border-red-800">ANOMALY</span>'
                            : '<span class="bg-emerald-950 text-emerald-400 px-2 py-1 rounded text-xs">Normal</span>';
                        
                        tr.innerHTML = `
                            <td class="p-3 font-medium text-slate-200">${row.transponder_id}</td>
                            <td class="p-3">${row.carrier_power_dbm}</td>
                            <td class="p-3">${row.snr_db}</td>
                            <td class="p-3">${statusBadge}</td>
                        `;
                        tbody.appendChild(tr);
                    });

                    // Render Alert Cards
                    const alertContainer = document.getElementById('alerts-container');
                    if (data.recent_alerts.length > 0) {
                        alertContainer.innerHTML = '';
                        data.recent_alerts.forEach(alert => {
                            const div = document.createElement('div');
                            div.className = "bg-red-950/40 border border-red-900/60 p-4 rounded-lg text-sm";
                            div.innerHTML = `
                                <div class="flex justify-between font-bold text-red-400">
                                    <span>⚠️ ${alert.transponder_id}</span>
                                    <span class="text-xs text-slate-400">Trigger: ${alert.trigger_source}</span>
                                </div>
                                <p class="text-slate-300 mt-1 text-xs font-mono">Details: ${alert.details}</p>
                            `;
                            alertContainer.appendChild(div);
                        });
                        document.getElementById('stat-status').innerText = "ALERT ACTIVE";
                        document.getElementById('stat-status').className = "text-3xl font-bold mt-2 text-red-500";
                    }
                } catch (err) {
                    console.error("Failed to fetch dashboard data:", err);
                }
            }

            // Poll API every 2 seconds
            setInterval(fetchData, 2000);
            fetchData();
        </script>
        
        <!-- Load External Live Spectrum Chart Script -->
        <script src="/static/js/live_spectrum.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/summary")
def get_dashboard_summary():
    """
    API endpoint returning telemetry logs and alerts summary for UI polling.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch recent telemetry logs
        cursor.execute("SELECT * FROM telemetry_logs ORDER BY id DESC LIMIT 15")
        telemetry_rows = [dict(row) for row in cursor.fetchall()]

        # Fetch recent alerts
        cursor.execute("SELECT * FROM anomaly_alerts ORDER BY id DESC LIMIT 10")
        alert_rows = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT COUNT(*) as count FROM anomaly_alerts")
        total_alerts = cursor.fetchone()["count"]

        conn.close()

        return {
            "total_alerts": total_alerts,
            "recent_telemetry": telemetry_rows,
            "recent_alerts": alert_rows
        }
    except Exception as e:
        return {"total_alerts": 0, "recent_telemetry": [], "recent_alerts": [], "error": str(e)}
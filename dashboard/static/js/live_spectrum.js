// Live RF Spectrum & Telemetry Trend Visualizer using Chart.js

let spectrumChartInstance = null;

function initializeSpectrumChart() {
    const canvasElement = document.getElementById('spectrumChart');
    if (!canvasElement) {
        console.warn("Canvas element with ID 'spectrumChart' not found in DOM.");
        return;
    }

    const ctx = canvasElement.getContext('2d');
    
    spectrumChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [], // Timestamps
            datasets: [
                {
                    label: 'Carrier Power (dBm)',
                    data: [],
                    borderColor: '#6366f1', // Indigo-500
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    yAxisID: 'y'
                },
                {
                    label: 'SNR (dB)',
                    data: [],
                    borderColor: '#10b981', // Emerald-500
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.3,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false, // Disable for smooth high-frequency streaming
            scales: {
                x: {
                    grid: { color: 'rgba(51, 65, 85, 0.3)' },
                    ticks: { color: '#94a3b8', font: { size: 10 } }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: { display: true, text: 'Power (dBm)', color: '#6366f1' },
                    grid: { color: 'rgba(51, 65, 85, 0.3)' },
                    ticks: { color: '#94a3b8' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: { display: true, text: 'SNR (dB)', color: '#10b981' },
                    grid: { drawOnChartArea: false }, // Prevent overlapping grid lines
                    ticks: { color: '#94a3b8' }
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#f8fafc', font: { size: 12 } }
                }
            }
        }
    });
}

async function updateSpectrumChart() {
    if (!spectrumChartInstance) return;

    try {
        const response = await fetch('/api/summary');
        const data = await response.json();
        
        if (!data.recent_telemetry || data.recent_telemetry.length === 0) return;

        // Take the latest records and reverse them for chronological left-to-right plotting
        const records = [...data.recent_telemetry].reverse().slice(-20);
        
        const labels = records.map(r => {
            const date = new Date(r.timestamp * 1000);
            return date.toLocaleTimeString();
        });
        
        const powerData = records.map(r => r.carrier_power_dbm);
        const snrData = records.map(r => r.snr_db);

        spectrumChartInstance.data.labels = labels;
        spectrumChartInstance.data.datasets[0].data = powerData;
        spectrumChartInstance.data.datasets[1].data = snrData;
        
        spectrumChartInstance.update();
    } catch (err) {
        console.error("Failed to update live spectrum chart:", err);
    }
}

// Automatically initialize and set interval poll on page load
document.addEventListener("DOMContentLoaded", () => {
    initializeSpectrumChart();
    setInterval(updateSpectrumChart, 2000);
});
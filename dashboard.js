document.addEventListener("DOMContentLoaded", function () {

    // =========================
    // 🔹 LIVE CLOCK
    // =========================
    function startLiveClock() {

        function updateClock() {

            const now = new Date();

            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const seconds = String(now.getSeconds()).padStart(2, '0');

            const clock =
                document.getElementById("live-clock");

            if (clock) {
                clock.innerText =
                    `${hours}:${minutes}:${seconds}`;
            }
        }

        updateClock();

        setInterval(updateClock, 1000);
    }

    startLiveClock();

    // =========================
    // 🔹 CHART CONFIG
    // =========================
    Chart.defaults.color = "#9ca3af";

    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,

        plugins: {
            legend: {
                display: false
            }
        },

        scales: {
            x: {
                ticks: { color: "#9ca3af" },
                grid: { display: false }
            },

            y: {
                ticks: { color: "#9ca3af" },
                grid: {
                    color: "rgba(255,255,255,0.05)"
                }
            }
        }
    };

    // =========================
    // 🔹 TEMPERATURE CHART
    // =========================
    const tempChart = new Chart(
        document.getElementById("tempChart"),

        {
            type: "line",

            data: {
                labels: [],
                datasets: [{
                    label: "Temperature",

                    data: [],

                    borderColor: "#f97316",

                    backgroundColor:
                        "rgba(249,115,22,0.1)",

                    fill: true,
                    tension: 0.4
                }]
            },

            options: commonOptions
        }
    );

    // =========================
    // 🔹 SALINITY CHART
    // =========================
    const salinityChart = new Chart(
        document.getElementById("salinityChart"),

        {
            type: "line",

            data: {
                labels: [],

                datasets: [{
                    label: "Salinity",

                    data: [],

                    borderColor: "#22d3ee",

                    backgroundColor:
                        "rgba(34,211,238,0.1)",

                    fill: true,
                    tension: 0.4
                }]
            },

            options: commonOptions
        }
    );

    // =========================
    // 🔹 OXYGEN CHART
    // =========================
    const oxygenChart = new Chart(
        document.getElementById("oxygenChart"),

        {
            type: "line",

            data: {
                labels: [],

                datasets: [{
                    label: "Oxygen",

                    data: [],

                    borderColor: "#10b981",

                    backgroundColor:
                        "rgba(16,185,129,0.1)",

                    fill: true,
                    tension: 0.4
                }]
            },

            options: commonOptions
        }
    );

    // =========================
    // 🔹 ADVISORY CHART
    // =========================
    const advisoryChart = new Chart(
        document.getElementById("advisoryChart"),

        {
            type: "doughnut",

            data: {
                labels: [
                    "Safe",
                    "Restricted",
                    "Danger"
                ],

                datasets: [{
                    data: [70, 20, 10],

                    backgroundColor: [
                        "#10b981",
                        "#fbbf24",
                        "#ef4444"
                    ],

                    borderWidth: 0
                }]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        labels: {
                            color: "#9ca3af"
                        }
                    }
                }
            }
        }
    );

    // =========================
    // 🔹 LOAD OCEAN DATA
    // =========================
    async function loadOceanData() {

        try {

            const locationSelect =
                document.getElementById(
                    "location-select"
                );

            const location =
                locationSelect
                ? locationSelect.value
                : "mumbai";

            const res = await fetch(
                `http://127.0.0.1:8000/api/ocean-data?location=${location}`
            );

            const data = await res.json();

            console.log("🌊 API:", data);

            const ocean = data.data;
            const history = data.history;

            // =========================
            // 🔹 UPDATE CARDS
            // =========================
            document.getElementById(
                "temp-value"
            ).innerText =
                ocean.temperature.toFixed(2) + " °C";

            document.getElementById(
                "salinity-value"
            ).innerText =
                ocean.salinity.toFixed(2) + " PSU";

            document.getElementById(
                "oxygen-value"
            ).innerText =
                ocean.oxygen.toFixed(2) + " mg/L";

            document.getElementById(
                "risk-level"
            ).innerText =
                ocean.riskLevel;

            document.getElementById(
                "riskScore"
            ).innerText =
                ocean.riskScore;

            document.getElementById(
                "sea-level"
            ).innerText =
                ocean.seaLevel.toFixed(2) + " m";

            // =========================
            // 🔹 UPDATE TIME
            // =========================
            const timeElement =
                document.getElementById(
                    "update-time"
                );

            if (timeElement) {

                timeElement.innerText =
                    "Last updated: " +
                    new Date(
                        data.timestamp
                    ).toLocaleTimeString();
            }

            // =========================
            // 🔹 UPDATE CHARTS
            // =========================
            tempChart.data.labels =
                history.timestamps;

            tempChart.data.datasets[0].data =
                history.temperature;

            tempChart.update();

            salinityChart.data.labels =
                history.timestamps;

            salinityChart.data.datasets[0].data =
                history.salinity;

            salinityChart.update();

            oxygenChart.data.labels =
                history.timestamps;

            oxygenChart.data.datasets[0].data =
                history.oxygen;

            oxygenChart.update();

            // =========================
            // 🔹 ADVISORY STATUS
            // =========================
            document.getElementById(
    "wave-height"
).innerText =
    ocean.waveHeight.toFixed(2) + " m";

document.getElementById(
    "wind-speed"
).innerText =
    ocean.windSpeed.toFixed(2) + " km/h";

document.getElementById(
    "wave-bar"
).style.width =
    `${Math.min(ocean.waveHeight * 30, 100)}%`;

document.getElementById(
    "wind-bar"
).style.width =
    `${Math.min(ocean.windSpeed * 4, 100)}%`;

const advisoryEl =
    document.getElementById(
        "advisory-status"
    );

advisoryEl.innerText =
    ocean.advisory;

if (ocean.advisory === "Safe") {

    advisoryEl.className =
        "px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-sm";
}

else if (
    ocean.advisory === "Restricted"
) {

    advisoryEl.className =
        "px-3 py-1 rounded-full bg-yellow-500/20 text-yellow-400 text-sm";
}

else {

    advisoryEl.className =
        "px-3 py-1 rounded-full bg-red-500/20 text-red-400 text-sm";
}
            // =========================
            // 🔹 CLUSTERS
            // =========================
            const clusterContainer =
    document.getElementById(
        "cluster-container"
    );

if (
    clusterContainer &&
    ocean.clusters
) {

    clusterContainer.innerHTML = "";

    ocean.clusters.forEach(
        cluster => {

        let color =
            "emerald";

        if (
            cluster.risk === "Medium"
        ) {
            color = "yellow";
        }

        if (
            cluster.risk === "High"
        ) {
            color = "red";
        }

        clusterContainer.innerHTML += `

            <div class="
                p-4 rounded-xl
                bg-white/5
                border border-${color}-500/30
            ">

                <div class="
                    flex justify-between items-center
                ">

                    <span class="text-white font-medium">
                        ${cluster.zone}
                    </span>

                    <span class="
                        px-2 py-1 rounded-full
                        text-xs
                        bg-${color}-500/20
                        text-${color}-400
                    ">
                        ${cluster.risk}
                    </span>

                </div>

            </div>
        `;
    });
}
            // =========================
            // 🔹 RISK METER
            // =========================
            const riskCircle =
                document.getElementById(
                    "risk-progress"
                );

            if (riskCircle) {

                const radius = 70;

                const circumference =
                    2 * Math.PI * radius;

                const offset =
                    circumference -
                    (ocean.riskScore / 100)
                    * circumference;

                riskCircle.style.strokeDashoffset =
                    offset;
            }

        } catch (error) {

            console.error(
                "❌ Dashboard Error:",
                error
            );
        }
    }

    // =========================
    // 🔹 DROPDOWN
    // =========================
    const locationSelect =
        document.getElementById(
            "location-select"
        );

    if (locationSelect) {

        locationSelect.addEventListener(
            "change",
            loadOceanData
        );
    }
    // =========================
    // 🔹 INIT
    // =========================
    loadOceanData();

    setInterval(loadOceanData, 5000);

});
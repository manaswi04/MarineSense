// ============================================================
// MarineSense Dashboard
// ============================================================

console.log("🌊 MarineSense dashboard.js loaded");

// ============================================================
// CONFIG
// ============================================================

const API_BASE =
    "http://127.0.0.1:8000";

// ============================================================
// CHART VARIABLES
// ============================================================

let tempChart = null;
let salinityChart = null;
let currentChart = null;

// ============================================================
// SAFE NUMBER
// ============================================================

function safeNumber(value, fallback = 0) {

    const number = Number(value);

    return Number.isFinite(number)
        ? number
        : fallback;
}

// ============================================================
// FORMAT TIME
// ============================================================

function formatGraphTime(value) {

    if (!value) {
        return "";
    }

    try {

        // Backend:
        // 2026-08-20T11:00

        if (value.includes("T")) {

            return value
                .split("T")[1]
                .substring(0, 5);
        }

        return value;

    } catch (error) {

        return value;
    }
}

// ============================================================
// GET ELEMENT
// ============================================================

function getElement(id) {

    return document.getElementById(id);
}

// ============================================================
// UPDATE TEXT
// ============================================================

function setText(id, value) {

    const element = getElement(id);

    if (element) {
        element.textContent = value;
    }
}

// ============================================================
// CREATE CHART OPTIONS
// ============================================================

function chartOptions() {

    return {

        responsive: true,

        maintainAspectRatio: false,

        animation: false,

        interaction: {
            intersect: false,
            mode: "index"
        },

        plugins: {

            legend: {
                labels: {
                    color: "#d1d5db"
                }
            }

        },

        scales: {

            x: {

                ticks: {
                    color: "#9ca3af"
                },

                grid: {
                    color: "rgba(255,255,255,0.05)"
                }

            },

            y: {

                ticks: {
                    color: "#9ca3af"
                },

                grid: {
                    color: "rgba(255,255,255,0.05)"
                },

                beginAtZero: false

            }

        }

    };
}

// ============================================================
// DESTROY OLD CHARTS
// ============================================================

function destroyCharts() {

    if (tempChart) {

        tempChart.destroy();
        tempChart = null;

    }

    if (salinityChart) {

        salinityChart.destroy();
        salinityChart = null;

    }

    if (currentChart) {

        currentChart.destroy();
        currentChart = null;

    }

}

// ============================================================
// INITIALIZE CHARTS
// ============================================================

function initializeCharts() {

    console.log("📊 Initializing charts...");

    if (typeof Chart === "undefined") {

        console.error(
            "❌ Chart.js is not loaded"
        );

        return false;
    }

    const tempCanvas =
        getElement("tempChart");

    const salinityCanvas =
        getElement("salinityChart");

    const currentCanvas =
        getElement("oxygenChart");

    console.log(
        "Canvas:",
        {
            tempCanvas,
            salinityCanvas,
            currentCanvas
        }
    );

    if (!tempCanvas) {

        console.error(
            "❌ tempChart canvas not found"
        );

        return false;
    }

    if (!salinityCanvas) {

        console.error(
            "❌ salinityChart canvas not found"
        );

        return false;
    }

    if (!currentCanvas) {

        console.error(
            "❌ oxygenChart canvas not found"
        );

        return false;
    }

    destroyCharts();

    // ========================================================
    // TEMPERATURE
    // ========================================================

    tempChart = new Chart(
        tempCanvas,
        {

            type: "line",

            data: {

                labels: [],

                datasets: [

                    {

                        label: "Sea Temperature (°C)",

                        data: [],

                        borderColor: "#22d3ee",

                        backgroundColor:
                            "rgba(34,211,238,0.10)",

                        borderWidth: 2,

                        fill: true,

                        tension: 0.35,

                        pointRadius: 4,

                        pointHoverRadius: 6

                    }

                ]

            },

            options: chartOptions()

        }
    );

    // ========================================================
    // SALINITY
    // ========================================================

    salinityChart = new Chart(
        salinityCanvas,
        {

            type: "line",

            data: {

                labels: [],

                datasets: [

                    {

                        label: "Salinity (PSU)",

                        data: [],

                        borderColor: "#60a5fa",

                        backgroundColor:
                            "rgba(96,165,250,0.10)",

                        borderWidth: 2,

                        fill: true,

                        tension: 0.35,

                        pointRadius: 4,

                        pointHoverRadius: 6

                    }

                ]

            },

            options: chartOptions()

        }
    );

    // ========================================================
    // OCEAN CURRENT
    // ========================================================

    currentChart = new Chart(
        currentCanvas,
        {

            type: "line",

            data: {

                labels: [],

                datasets: [

                    {

                        label:
                            "Ocean Current Velocity (m/s)",

                        data: [],

                        borderColor: "#34d399",

                        backgroundColor:
                            "rgba(52,211,153,0.10)",

                        borderWidth: 2,

                        fill: true,

                        tension: 0.35,

                        pointRadius: 4,

                        pointHoverRadius: 6

                    }

                ]

            },

            options: chartOptions()

        }
    );

    console.log(
        "✅ Charts initialized"
    );

    return true;
}

// ============================================================
// UPDATE CHARTS
// ============================================================

function updateCharts(history) {

    if (!Array.isArray(history)) {

        console.error(
            "❌ History is not an array:",
            history
        );

        return;
    }

    if (
        !tempChart ||
        !salinityChart ||
        !currentChart
    ) {

        console.warn(
            "⚠️ Charts not initialized. Initializing..."
        );

        if (!initializeCharts()) {
            return;
        }
    }

    // ========================================================
    // LABELS
    // ========================================================

    const labels =
        history.map(
            point =>
                formatGraphTime(point.time)
        );

    // ========================================================
    // TEMPERATURE
    // ========================================================

    const temperatures =
        history.map(
            point =>
                safeNumber(
                    point.temperature
                )
        );

    // ========================================================
    // SALINITY
    // ========================================================

    const salinities =
        history.map(
            point =>
                safeNumber(
                    point.salinity
                )
        );

    // ========================================================
    // CURRENT VELOCITY
    // ========================================================

    const currents =
        history.map(
            point =>
                safeNumber(
                    point.currentVelocity
                )
        );

    console.log(
        "📈 Chart data:",
        {
            labels,
            temperatures,
            salinities,
            currents
        }
    );

    // ========================================================
    // UPDATE TEMPERATURE
    // ========================================================

    tempChart.data.labels = labels;

    tempChart.data.datasets[0].data =
        temperatures;

    tempChart.update();

    // ========================================================
    // UPDATE SALINITY
    // ========================================================

    salinityChart.data.labels = labels;

    salinityChart.data.datasets[0].data =
        salinities;

    salinityChart.update();

    // ========================================================
    // UPDATE CURRENT
    // ========================================================

    currentChart.data.labels = labels;

    currentChart.data.datasets[0].data =
        currents;

    currentChart.update();

    console.log(
        "✅ All graphs updated"
    );
}

// ============================================================
// UPDATE DASHBOARD CARDS
// ============================================================

function updateDashboardCards(ocean, data) {

    console.log(
        "📊 Updating dashboard cards:",
        ocean
    );

    // ========================================================
    // TEMPERATURE
    // ========================================================

    const temperature =
        safeNumber(
            ocean.temperature
        );

    setText(
        "temp-value",
        temperature.toFixed(2) + " °C"
    );

    // ========================================================
    // SALINITY
    // ========================================================

    const salinity =
        safeNumber(
            ocean.salinity
        );

    setText(
        "salinity-value",
        salinity.toFixed(2) + " PSU"
    );

    // ========================================================
    // OCEAN CURRENT
    // ========================================================

    const currentVelocity =
        safeNumber(
            ocean.currentVelocity
        );

    setText(
        "oxygen-value",
        currentVelocity.toFixed(2) + " m/s"
    );

    // ========================================================
    // RISK LEVEL
    // ========================================================

    const riskLevel =
        ocean.riskLevel || "Unknown";

    setText(
        "risk-level",
        riskLevel
    );

    // ========================================================
    // SEA LEVEL
    // ========================================================

    const seaLevel =
        safeNumber(
            ocean.seaLevel
        );

    setText(
        "sea-level",
        seaLevel.toFixed(2) + " m"
    );

    // ========================================================
    // WAVE HEIGHT
    // ========================================================

    const waveHeight =
        safeNumber(
            ocean.waveHeight
        );

    setText(
        "wave-height",
        waveHeight.toFixed(2) + " m"
    );

    // ========================================================
    // WAVE BAR
    // ========================================================

    const waveBar =
        getElement("wave-bar");

    if (waveBar) {

        const wavePercent =
            Math.min(
                (waveHeight / 4) * 100,
                100
            );

        waveBar.style.width =
            wavePercent + "%";
    }

    // ========================================================
    // WIND SPEED
    // ========================================================

    const windSpeed =
        safeNumber(
            ocean.windSpeed
        );

    setText(
        "wind-speed",
        windSpeed.toFixed(1) + " km/h"
    );

    // ========================================================
    // WIND BAR
    // ========================================================

    const windBar =
        getElement("wind-bar");

    if (windBar) {

        const windPercent =
            Math.min(
                (windSpeed / 40) * 100,
                100
            );

        windBar.style.width =
            windPercent + "%";
    }

    // ========================================================
    // ADVISORY
    // ========================================================

    const advisory =
        ocean.advisory || "Safe";

    const advisoryElement =
        getElement("advisory-status");

    if (advisoryElement) {

        advisoryElement.textContent =
            advisory.toUpperCase();

        advisoryElement.className =
            "px-3 py-1 rounded-full text-sm";

        if (advisory === "Danger") {

            advisoryElement.classList.add(
                "bg-red-500/20",
                "text-red-400"
            );

        } else if (
            advisory === "Restricted"
        ) {

            advisoryElement.classList.add(
                "bg-yellow-500/20",
                "text-yellow-400"
            );

        } else {

            advisoryElement.classList.add(
                "bg-emerald-500/20",
                "text-emerald-400"
            );
        }
    }

    // ========================================================
    // RISK SCORE
    // ========================================================

    const riskScore =
        safeNumber(
            ocean.riskScore
        );

    setText(
        "riskScore",
        Math.round(riskScore)
    );

    // ========================================================
    // RISK LABEL
    // ========================================================

    setText(
        "risk-label",
        riskLevel.toUpperCase()
    );

    // ========================================================
    // RISK CIRCLE
    // ========================================================

    const riskProgress =
        getElement("risk-progress");

    if (riskProgress) {

        const circumference = 440;

        const offset =
            circumference -
            (
                riskScore / 100
            ) * circumference;

        riskProgress.style.strokeDashoffset =
            offset;
    }

    // ========================================================
    // LOCATION LABELS
    // ========================================================

    const locationName =
        data.locationName ||
        "Marine Location";

    document
        .querySelectorAll(
            "#dashboard-page span"
        )
        .forEach(
            element => {

                const text =
                    element.textContent
                        .trim();

                if (
                    text === "Mumbai Port"
                ) {

                    element.textContent =
                        locationName;
                }

            }
        );

    // ========================================================
    // CLUSTERS
    // ========================================================

    updateClusters(
        ocean.clusters
    );

    // ========================================================
    // LAST UPDATED
    // ========================================================

    const updateTime =
        getElement("update-time");

    if (updateTime) {

        if (data.timestamp) {

            const time =
                new Date(
                    data.timestamp
                );

            if (
                !Number.isNaN(
                    time.getTime()
                )
            ) {

                updateTime.textContent =
                    "Updated: " +
                    time.toLocaleTimeString(
                        "en-IN",
                        {
                            hour: "2-digit",
                            minute: "2-digit",
                            second: "2-digit"
                        }
                    );

            } else {

                updateTime.textContent =
                    "Live data";

            }

        } else {

            updateTime.textContent =
                "Live data";
        }
    }
}

// ============================================================
// CLUSTERS
// ============================================================

function updateClusters(clusters) {

    const container =
        getElement(
            "cluster-container"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (
        !Array.isArray(clusters) ||
        clusters.length === 0
    ) {

        container.innerHTML = `
            <div class="glass-effect rounded-xl p-4">
                <p class="text-gray-400 text-sm">
                    No zone data available
                </p>
            </div>
        `;

        return;
    }

    clusters.forEach(
        cluster => {

            let badgeClass =
                "bg-emerald-500/20 text-emerald-400";

            if (
                cluster.risk === "Medium"
            ) {

                badgeClass =
                    "bg-yellow-500/20 text-yellow-400";

            } else if (
                cluster.risk === "High"
            ) {

                badgeClass =
                    "bg-red-500/20 text-red-400";
            }

            container.innerHTML += `

                <div class="
                    glass-effect
                    rounded-xl
                    p-4
                    flex
                    justify-between
                    items-center
                ">

                    <span class="text-gray-300">
                        ${cluster.zone || "Zone"}
                    </span>

                    <span class="
                        px-3
                        py-1
                        rounded-full
                        text-xs
                        ${badgeClass}
                    ">
                        ${cluster.risk || "Unknown"}
                    </span>

                </div>

            `;
        }
    );
}
// ============================================================
// GET SELECTED LOCATION
// (shared priority order — matches risk.js / advisory.js / biodiversity.js)
// ============================================================

function getSelectedLocation() {

    if (
        typeof window.selectedLocation !== "undefined" &&
        window.selectedLocation
    ) {
        return String(window.selectedLocation).toLowerCase().trim();
    }

    const storedLocation = localStorage.getItem("selectedLocation");

    if (storedLocation) {
        return storedLocation.toLowerCase().trim();
    }

    const locationSelect = getElement("location-select");

    if (locationSelect && locationSelect.value) {
        return locationSelect.value.toLowerCase().trim();
    }

    return "mumbai";
}

// ============================================================
// LOAD OCEAN DATA
// ============================================================

async function loadOceanData() {

    try {

        const location = getSelectedLocation();

        console.log(
            "🌊 Loading ocean data:",
            location
        );

        const url =
            `${API_BASE}/api/ocean-data?location=${encodeURIComponent(location)}`;

        const response =
            await fetch(
                url,
                {
                    method: "GET",
                    cache: "no-store"
                }
            );

        console.log(
            "🌐 Ocean API status:",
            response.status
        );

        if (!response.ok) {

            throw new Error(
                `Ocean API returned HTTP ${response.status}`
            );
        }

        const data =
            await response.json();

        console.log(
            "🌊 Ocean API response:",
            data
        );

        if (
            !data ||
            !data.data
        ) {

            throw new Error(
                "Invalid ocean API response"
            );
        }

        const history =
            Array.isArray(
                data.history
            )
                ? data.history
                : [];

        // ====================================================
        // UPDATE CARDS
        // ====================================================

        updateDashboardCards(
            data.data,
            data
        );

        // ====================================================
        // UPDATE GRAPHS
        // ====================================================

        updateCharts(
            history
        );

        console.log(
            "✅ Dashboard loaded successfully"
        );

    } catch (error) {

        console.error(
            "❌ Dashboard loading error:",
            error
        );

        const updateTime =
            getElement(
                "update-time"
            );

        if (updateTime) {

            updateTime.textContent =
                "Unable to load live data";
        }
    }
}

// ============================================================
// LOCATION CHANGE
// ============================================================

function setupLocationSelector() {

    const selector =
        getElement("location-select");

    if (!selector) {

        console.warn(
            "⚠️ location-select not found"
        );

        return;
    }

    selector.addEventListener(
        "change",
        async function () {

            const location = this.value.toLowerCase().trim();

            window.selectedLocation = location;
            localStorage.setItem("selectedLocation", location);

            console.log("📍 Location changed:", location);

            await loadOceanData();
        }
    );
}

// ============================================================
// LIVE CLOCK
// ============================================================

function startClock() {

    const clock =
        getElement(
            "live-clock"
        );

    if (!clock) {
        return;
    }

    function updateClock() {

        const now =
            new Date();

        clock.textContent =
            now.toLocaleTimeString(
                "en-IN",
                {
                    hour12: false
                }
            );
    }

    updateClock();

    setInterval(
        updateClock,
        1000
    );
}

// ============================================================
// INITIALIZE DASHBOARD
// ============================================================

async function initializeDashboard() {

    console.log(
        "🚀 Initializing MarineSense dashboard..."
    );

    initializeCharts();

    setupLocationSelector();

    startClock();

    await loadOceanData();

}

// ============================================================
// DOM READY
// ============================================================

if (
    document.readyState === "loading"
) {

    document.addEventListener(
        "DOMContentLoaded",
        initializeDashboard
    );

} else {

    initializeDashboard();

}

// ============================================================
// OPTIONAL GLOBAL ACCESS
// ============================================================

window.loadOceanData =
    loadOceanData;

window.initializeDashboard =
    initializeDashboard;
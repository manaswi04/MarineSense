// =============================================
// MarineSense — Marine Advisory Engine
// =============================================

document.addEventListener("DOMContentLoaded", () => {
    const API_BASE = "http://127.0.0.1:8000";
    const REFRESH_INTERVAL = 60000;
    const REQUEST_TIMEOUT = 30000;

    let requestInProgress = false;
    let refreshTimer = null;
    let activeController = null;

    // ---------------------------------------------
    // HELPERS
    // ---------------------------------------------

    function getSelectedLocation() {
        const selected =
            window.selectedLocation ||
            localStorage.getItem("selectedLocation") ||
            "mumbai";

        return String(selected).toLowerCase().trim();
    }

    function formatValue(value, decimals = 2, unit = "") {
        if (
            value === null ||
            value === undefined ||
            value === "" ||
            !Number.isFinite(Number(value))
        ) {
            return "--";
        }

        return `${Number(value).toFixed(decimals)}${unit ? " " + unit : ""}`;
    }

    function setText(id, value) {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    }

    function showError(message) {
        const container = document.getElementById("advisory-cards");
        if (!container) return;

        container.replaceChildren();

        const card = document.createElement("div");
        card.className =
            "glass-effect rounded-2xl p-6 border border-red-500/30";

        const heading = document.createElement("h3");
        heading.className = "text-xl font-bold text-red-400 mb-2";
        heading.textContent = "Unable to load advisory data";

        const detail = document.createElement("p");
        detail.className = "text-gray-300";
        detail.textContent = message;

        card.append(heading, detail);
        container.appendChild(card);
    }

    // ---------------------------------------------
    // ADVISORY CARD RENDERING
    // ---------------------------------------------

    function renderAdvisories(advisories) {
        const container = document.getElementById("advisory-cards");
        if (!container) return;

        container.replaceChildren();

        if (!Array.isArray(advisories) || advisories.length === 0) {
            const card = document.createElement("div");
            card.className =
                "glass-effect rounded-2xl p-6 border border-cyan-500/20";

            const heading = document.createElement("h3");
            heading.className = "text-xl font-bold text-white mb-2";
            heading.textContent = "No Advisory Messages";

            const message = document.createElement("p");
            message.className = "text-gray-300";
            message.textContent =
                "No advisory messages were returned. Check data availability before assuming conditions are stable.";

            card.append(heading, message);
            container.appendChild(card);
            return;
        }

        advisories.forEach((advisory) => {
            const severity = String(advisory.severity || "Unknown");

            let color = "cyan";
            if (severity === "Critical") color = "orange";
            else if (severity === "High") color = "red";
            else if (severity === "Medium") color = "amber";
            else if (severity === "Low") color = "emerald";

            const card = document.createElement("div");
            card.className =
                `glass-effect rounded-2xl p-6 border border-${color}-500/20`;

            const header = document.createElement("div");
            header.className =
                "flex justify-between items-start mb-4 gap-3";

            const titleGroup = document.createElement("div");

            const type = document.createElement("p");
            type.className =
                `text-xs uppercase text-${color}-400 mb-2`;
            type.textContent = advisory.type || "Marine Advisory";

            const title = document.createElement("h3");
            title.className = "text-xl font-bold text-white";
            title.textContent = advisory.title || "Marine Condition";

            titleGroup.append(type, title);

            const badge = document.createElement("span");
            badge.className =
                `px-3 py-1 rounded-full bg-${color}-500/20 text-${color}-400 text-xs`;
            badge.textContent = severity;

            header.append(titleGroup, badge);

            const message = document.createElement("p");
            message.className = "text-gray-300 mb-4";
            message.textContent = advisory.message || "";

            const recommendationBox = document.createElement("div");
            recommendationBox.className =
                "p-3 rounded-xl bg-white/5";

            const recommendationLabel = document.createElement("p");
            recommendationLabel.className =
                "text-xs text-gray-500 mb-1";
            recommendationLabel.textContent = "Recommendation";

            const recommendation = document.createElement("p");
            recommendation.className = "text-sm text-cyan-300";
            recommendation.textContent =
                advisory.recommendation || "Continue monitoring available data.";

            recommendationBox.append(
                recommendationLabel,
                recommendation
            );

            card.append(header, message, recommendationBox);
            container.appendChild(card);
        });
    }

    // ---------------------------------------------
    // LOAD ADVISORY DATA
    // ---------------------------------------------

    async function loadAdvisories() {
        if (requestInProgress) return;

        requestInProgress = true;
        activeController = new AbortController();

        const timeoutId = setTimeout(
            () => activeController?.abort(),
            REQUEST_TIMEOUT
        );

        try {
            const selectedLocation = getSelectedLocation();

            console.log("Advisory selected location:", selectedLocation);

            const apiUrl =
                `${API_BASE}/api/advisory?location=${encodeURIComponent(selectedLocation)}`;

            const response = await fetch(apiUrl, {
                cache: "no-store",
                signal: activeController.signal
            });

            if (!response.ok) {
                throw new Error(`Advisory API returned ${response.status}`);
            }

            const data = await response.json();

            console.log("Advisory API response:", data);

            if (data.status !== "success") {
                throw new Error(data.message || "Advisory API failed");
            }

            const summary = data.summary || {};

            // Risk score
            setText(
                "adv-risk-score",
                formatValue(summary.riskScore, 0)
            );

            // Wave height
            setText(
                "adv-wave",
                formatValue(summary.waveHeight, 2, "m")
            );

            // Oxygen is not supplied by the current API.
            setText("adv-oxygen", "--");

            // Temperature
            setText(
                "adv-temp",
                formatValue(summary.temperature, 2, "°C")
            );

            // Sea level
            setText(
                "adv-sea",
                formatValue(summary.seaLevel, 2, "m")
            );

            // Current velocity
            setText(
                "adv-current",
                formatValue(summary.currentVelocity, 2, "m/s")
            );

            // Salinity
            setText(
                "adv-salinity",
                formatValue(summary.salinity, 2, "PSU")
            );

            // Selected port
            setText(
                "adv-location",
                data.locationName || selectedLocation
            );

            // Render advisory cards
            renderAdvisories(data.advisories);

            // Log data completeness
            if (data.dataComplete === false) {
                console.warn(
                    "Some marine measurements are unavailable:",
                    data.missingData || []
                );
            }

            console.log(
                "Advisory dashboard updated for:",
                data.locationName || selectedLocation
            );

        } catch (error) {
            console.error("Advisory error:", error);

            if (error.name === "AbortError") {
                showError(
                    "The request timed out. Check that the backend is running and retry."
                );
            } else {
                showError(error.message || "An unexpected error occurred.");
            }
        } finally {
            clearTimeout(timeoutId);
            activeController = null;
            requestInProgress = false;
        }
    }

    // ---------------------------------------------
    // INITIAL LOAD AND AUTO REFRESH
    // ---------------------------------------------

    loadAdvisories();

    refreshTimer = setInterval(
        loadAdvisories,
        REFRESH_INTERVAL
    );

    // Respond to the port selector if it dispatches this event.
    window.addEventListener("portChanged", () => {
        if (activeController) {
            activeController.abort();
        }

        // Let the active request finish its cleanup first.
        setTimeout(loadAdvisories, 50);
    });

    // ---------------------------------------------
    // DOWNLOAD PDF REPORT
    // ---------------------------------------------

    const downloadButton =
        document.getElementById("download-report-btn");

    if (downloadButton) {
        downloadButton.addEventListener("click", () => {
            window.open(
                `${API_BASE}/api/download-report`,
                "_blank",
                "noopener"
            );
        });
    }
});

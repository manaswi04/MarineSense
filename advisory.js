// =============================================
// 📢 Marine Advisory Engine
// =============================================

document.addEventListener("DOMContentLoaded", () => {

    async function loadAdvisories() {

        try {

            // =============================================
            // GET SELECTED LOCATION
            // =============================================

            let selectedLocation =
                localStorage.getItem("selectedLocation") || "mumbai";

            selectedLocation =
                selectedLocation.toLowerCase().trim();

            console.log(
                "📍 Advisory selected location:",
                selectedLocation
            );

            // =============================================
            // API URL
            // IMPORTANT: BACKTICKS ARE REQUIRED
            // =============================================

            const apiUrl =
                `http://127.0.0.1:8000/api/advisory?location=${encodeURIComponent(selectedLocation)}`;

            console.log(
                "📡 Advisory API URL:",
                apiUrl
            );

            const res = await fetch(apiUrl, {
                cache: "no-store"
            });

            if (!res.ok) {

                throw new Error(
                    `Advisory API returned ${res.status}`
                );
            }

            const data = await res.json();

            console.log(
                "📢 Advisory API response:",
                data
            );

            // =============================================
            // CHECK API STATUS
            // =============================================

            if (data.status !== "success") {

                throw new Error(
                    data.message || "Advisory API failed"
                );
            }

            // =============================================
            // SUMMARY
            // =============================================

            const summary =
                data.summary || {};

            // =============================================
            // RISK SCORE
            // =============================================

            const riskScoreElement =
                document.getElementById("adv-risk-score");

            if (riskScoreElement) {

                riskScoreElement.innerText =
                    summary.riskScore ?? "--";
            }

            // =============================================
            // WAVE HEIGHT
            // =============================================

            const waveElement =
                document.getElementById("adv-wave");

            if (waveElement) {

                waveElement.innerText =
                    `${Number(summary.waveHeight ?? 0).toFixed(2)} m`;
            }

            // =============================================
            // OXYGEN
            // =============================================
            // Your current API DOES NOT return oxygen.
            // Therefore do NOT call .toFixed() on summary.oxygen.

            const oxygenElement =
                document.getElementById("adv-oxygen");

            if (oxygenElement) {

                oxygenElement.innerText =
                    "--";
            }

            // =============================================
            // TEMPERATURE
            // =============================================

            const tempElement =
                document.getElementById("adv-temp");

            if (tempElement) {

                tempElement.innerText =
                    `${Number(summary.temperature ?? 0).toFixed(2)} °C`;
            }

            // =============================================
            // SEA LEVEL
            // =============================================

            const seaElement =
                document.getElementById("adv-sea");

            if (seaElement) {

                seaElement.innerText =
                    `${Number(summary.seaLevel ?? 0).toFixed(2)} m`;
            }

            // =============================================
            // CURRENT VELOCITY
            // =============================================

            const currentElement =
                document.getElementById("adv-current");

            if (currentElement) {

                currentElement.innerText =
                    `${Number(summary.currentVelocity ?? 0).toFixed(2)} m/s`;
            }

            // =============================================
            // SALINITY
            // =============================================

            const salinityElement =
                document.getElementById("adv-salinity");

            if (salinityElement) {

                salinityElement.innerText =
                    `${Number(summary.salinity ?? 0).toFixed(2)} PSU`;
            }

            // =============================================
            // LOCATION NAME
            // =============================================

            const locationElement =
                document.getElementById("adv-location");

            if (locationElement) {

                locationElement.innerText =
                    data.locationName || selectedLocation;
            }

            // =============================================
            // ADVISORY CARDS
            // =============================================

            const container =
                document.getElementById("advisory-cards");

            if (!container) {

                console.warn(
                    "⚠️ advisory-cards element not found"
                );

            } else {

                container.innerHTML = "";

                const advisories =
                    Array.isArray(data.advisories)
                        ? data.advisories
                        : [];

                // =============================================
                // NO ADVISORIES
                // =============================================

                if (advisories.length === 0) {

                    container.innerHTML = `
                        <div class="
                            glass-effect
                            rounded-2xl
                            p-6
                            border
                            border-cyan-500/20
                        ">

                            <h3 class="
                                text-xl
                                font-bold
                                text-white
                                mb-2
                            ">
                                No Active Advisories
                            </h3>

                            <p class="text-gray-300">
                                Marine conditions are currently
                                stable.
                            </p>

                        </div>
                    `;

                } else {

                    // =============================================
                    // RENDER ADVISORIES
                    // =============================================

                    advisories.forEach(advisory => {

                        let color = "cyan";

                        if (
                            advisory.severity === "High"
                        ) {
                            color = "red";
                        }

                        if (
                            advisory.severity === "Critical"
                        ) {
                            color = "orange";
                        }

                        if (
                            advisory.severity === "Low"
                        ) {
                            color = "emerald";
                        }

                        container.innerHTML += `

                            <div class="
                                glass-effect
                                rounded-2xl
                                p-6
                                border
                                border-${color}-500/20
                            ">

                                <div class="
                                    flex
                                    justify-between
                                    items-start
                                    mb-4
                                ">

                                    <div>

                                        <p class="
                                            text-xs
                                            uppercase
                                            text-${color}-400
                                            mb-2
                                        ">
                                            ${advisory.type || "Marine Advisory"}
                                        </p>

                                        <h3 class="
                                            text-xl
                                            font-bold
                                            text-white
                                        ">
                                            ${advisory.title || "Marine Condition"}
                                        </h3>

                                    </div>

                                    <span class="
                                        px-3
                                        py-1
                                        rounded-full
                                        bg-${color}-500/20
                                        text-${color}-400
                                        text-xs
                                    ">
                                        ${advisory.severity || "Low"}
                                    </span>

                                </div>

                                <p class="
                                    text-gray-300
                                    mb-4
                                ">
                                    ${advisory.message || ""}
                                </p>

                                <div class="
                                    p-3
                                    rounded-xl
                                    bg-white/5
                                ">

                                    <p class="
                                        text-xs
                                        text-gray-500
                                        mb-1
                                    ">
                                        Recommendation
                                    </p>

                                    <p class="
                                        text-sm
                                        text-cyan-300
                                    ">
                                        ${advisory.recommendation || ""}
                                    </p>

                                </div>

                            </div>
                        `;
                    });
                }
            }

            console.log(
                "✅ Advisory dashboard updated for:",
                data.locationName
            );

        } catch (error) {

            console.error(
                "❌ Advisory Error:",
                error
            );

            // =============================================
            // SHOW ERROR ON SCREEN
            // =============================================

            const container =
                document.getElementById("advisory-cards");

            if (container) {

                container.innerHTML = `
                    <div class="
                        glass-effect
                        rounded-2xl
                        p-6
                        border
                        border-red-500/30
                    ">

                        <h3 class="
                            text-xl
                            font-bold
                            text-red-400
                            mb-2
                        ">
                            Unable to load live data
                        </h3>

                        <p class="text-gray-300">
                            ${error.message}
                        </p>

                    </div>
                `;
            }
        }
    }

    // =============================================
    // INITIAL LOAD
    // =============================================

    loadAdvisories();

    // =============================================
    // AUTO REFRESH
    // =============================================

    setInterval(
        loadAdvisories,
        60000
    );
});


// =============================================
// 🔹 DOWNLOAD REPORT
// =============================================

document.addEventListener("DOMContentLoaded", () => {

    const downloadBtn =
        document.getElementById(
            "download-report-btn"
        );

    if (downloadBtn) {

        downloadBtn.addEventListener(
            "click",
            () => {

                window.open(
                    "http://127.0.0.1:8000/api/download-report",
                    "_blank"
                );

            }
        );
    }
});
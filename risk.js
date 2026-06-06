// =============================================
// ⚠️ MarineSense Risk Engine
// =============================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

    async function loadRiskData() {

        try {

            // =============================================
            // 🔹 FETCH API
            // =============================================
            const res = await fetch(
    "http://127.0.0.1:8000/api/risk-analysis"
);
        

            if (!res.ok) {

                throw new Error(
                    "Failed to load risk data"
                );
            }

            const data = await res.json();

            console.log(
                "⚠️ Risk API:",
                data
            );

            const risk = data;

            if (!risk) {

                throw new Error(
                    "Risk analysis missing"
                );
            }

            // =============================================
            // 🔹 TOP METRICS
            // =============================================
            document.getElementById(
                "critical-zones"
            ).innerText =
                risk.criticalZones;

            document.getElementById(
                "high-risk-events"
            ).innerText =
                risk.highRiskEvents;

            document.getElementById(
    "risk-score-avg"
).innerText =
    risk.riskScore;

            document.getElementById(
                "risk-trend"
            ).innerText =
                risk.trend;

            // =============================================
            // 🔹 PROGRESS BARS
            // =============================================
            document.getElementById(
                "critical-bar"
            ).style.width =
                `${risk.criticalZones * 30}%`;

            document.getElementById(
                "events-bar"
            ).style.width =
                `${risk.highRiskEvents * 4}%`;

            document.getElementById(
                "risk-score-bar"
            ).style.width =
                `${risk.riskScore}%`;

            // =============================================
            // 🔹 RISK FACTORS
            // =============================================
            const factorsContainer =
                document.getElementById(
                    "risk-factors"
                );

            if (factorsContainer) {

                factorsContainer.innerHTML = "";

                risk.factors.forEach(
                    factor => {

                    let color =
                        "yellow";

                    if (
                        factor.severity ===
                        "Critical"
                    ) {
                        color = "red";
                    }

                    if (
                        factor.severity ===
                        "Low"
                    ) {
                        color = "emerald";
                    }

                    factorsContainer.innerHTML += `

                        <div class="
                            flex items-center
                            justify-between
                            p-3 bg-white/5
                            rounded-lg
                        ">

                            <div>

                                <p class="
                                    text-sm
                                    text-gray-300
                                ">
                                    ${factor.title}
                                </p>

                                <p class="
                                    text-xs
                                    text-gray-500
                                ">
                                    ${factor.desc}
                                </p>

                            </div>

                            <div class="
                                text-right
                            ">

                                <p class="
                                    text-sm
                                    font-semibold
                                    text-${color}-400
                                ">
                                    ${factor.severity}
                                </p>

                                <div class="
                                    w-12 h-1
                                    bg-white/10
                                    rounded-full mt-1
                                ">

                                    <div class="
                                        h-full
                                        bg-${color}-500
                                        rounded-full
                                    "

                                    style="
                                        width:
                                        ${factor.value}%
                                    ">

                                    </div>

                                </div>

                            </div>

                        </div>
                    `;
                });
            }

            // =============================================
            // 🔹 ALERTS
            // =============================================
            const alertsContainer =
                document.getElementById(
                    "risk-alerts"
                );

            if (alertsContainer) {

                alertsContainer.innerHTML = "";

                risk.alerts.forEach(
                    alert => {

                    let color =
                        "cyan";

                    if (
                        alert.type ===
                        "ALERT"
                    ) {
                        color = "red";
                    }

                    if (
                        alert.type ===
                        "WARNING"
                    ) {
                        color = "yellow";
                    }

                    alertsContainer.innerHTML += `

                        <div class="
                            p-3
                            border-l-4
                            border-${color}-500
                            bg-${color}-500/10
                            rounded
                        ">

                            <p class="
                                text-xs
                                text-${color}-400
                                font-semibold
                            ">
                                ${alert.type}
                            </p>

                            <p class="
                                text-sm
                                text-gray-300
                                mt-1
                            ">
                                ${alert.message}
                            </p>

                            <p class="
                                text-xs
                                text-gray-500
                                mt-1
                            ">
                                ${alert.time}
                            </p>

                        </div>
                    `;
                });
            }

        } catch (error) {

            console.error(
                "❌ Risk Error:",
                error
            );
        }
    }


    // =============================================
    // 🔹 INITIAL LOAD
    // =============================================
    loadRiskData();

    // =============================================
    // 🔹 AUTO REFRESH
    // =============================================
    setInterval(
        loadRiskData,
        15000
    );
});
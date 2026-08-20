// =============================================
// ⚠️ MarineSense Risk Engine
// =============================================

document.addEventListener("DOMContentLoaded", () => {

    // =============================================
    // 🔹 GET SELECTED LOCATION
    // =============================================
    function getSelectedLocation() {

        // Try common global variable
        if (
            typeof window.selectedLocation !== "undefined" &&
            window.selectedLocation
        ) {
            return String(window.selectedLocation)
                .toLowerCase()
                .trim();
        }

        // Try localStorage
        const storedLocation =
            localStorage.getItem("selectedLocation");

        if (storedLocation) {
            return storedLocation
                .toLowerCase()
                .trim();
        }

        // Try port selector
        const selectors = [
            "#port-select",
            "#location-select",
            "#portSelector",
            "#locationSelector"
        ];

        for (const selector of selectors) {

            const element =
                document.querySelector(selector);

            if (
                element &&
                element.value
            ) {
                return element.value
                    .toLowerCase()
                    .trim();
            }
        }

        // Backend default
        return "mumbai";
    }


    // =============================================
    // 🔹 SAFE ELEMENT UPDATE
    // =============================================
    function setText(id, value) {

        const element =
            document.getElementById(id);

        if (element) {
            element.innerText =
                value ?? "--";
        }
    }


    // =============================================
    // 🔹 SAFE WIDTH UPDATE
    // =============================================
    function setWidth(id, value) {

        const element =
            document.getElementById(id);

        if (!element) {
            return;
        }

        let width =
            Number(value);

        if (!Number.isFinite(width)) {
            width = 0;
        }

        width =
            Math.max(
                0,
                Math.min(100, width)
            );

        element.style.width =
            `${width}%`;
    }


    // =============================================
    // 🔹 LOAD RISK DATA
    // =============================================
    async function loadRiskData() {

        try {

            const selectedLocation =
                getSelectedLocation();

            console.log(
                "⚠️ Risk selected location:",
                selectedLocation
            );


            // =============================================
            // 🔹 API URL
            // =============================================
            const apiUrl =
                `http://127.0.0.1:8000/api/risk-analysis?location=${encodeURIComponent(
                    selectedLocation
                )}`;

            console.log(
                "⚠️ Risk API URL:",
                apiUrl
            );


            // =============================================
            // 🔹 FETCH
            // =============================================
            const res =
                await fetch(
                    apiUrl,
                    {
                        cache: "no-store"
                    }
                );


            if (!res.ok) {

                throw new Error(
                    `Risk API returned ${res.status}`
                );
            }


            const risk =
                await res.json();


            console.log(
                "⚠️ Risk API response:",
                risk
            );


            if (
                !risk ||
                risk.status === "error"
            ) {

                throw new Error(
                    risk?.message ||
                    "Risk analysis data missing"
                );
            }


            // =============================================
            // 🔹 LOCATION
            // =============================================
            setText(
                "risk-location",
                risk.locationName
            );


            // =============================================
            // 🔹 TOP METRICS
            // =============================================

            setText(
                "critical-zones",
                risk.criticalZones ?? 0
            );


            /*
             * Your backend currently does NOT return
             * highRiskEvents.
             *
             * Calculate it from alerts instead.
             */

            const alerts =
                Array.isArray(risk.alerts)
                    ? risk.alerts
                    : [];

            const highRiskEvents =
                alerts.filter(
                    alert =>
                        alert.type === "ALERT" ||
                        alert.type === "WARNING"
                ).length;


            setText(
                "high-risk-events",
                highRiskEvents
            );


            setText(
                "risk-score-avg",
                risk.riskScore ?? 0
            );


            setText(
                "risk-trend",
                risk.trend ?? "--"
            );


            // =============================================
            // 🔹 RISK LEVEL
            // =============================================
            setText(
                "risk-level",
                risk.riskLevel ?? "--"
            );


            // =============================================
            // 🔹 PROGRESS BARS
            // =============================================

            const criticalZones =
                Number(
                    risk.criticalZones ?? 0
                );

            setWidth(
                "critical-bar",
                criticalZones * 30
            );


            setWidth(
                "events-bar",
                highRiskEvents * 25
            );


            setWidth(
                "risk-score-bar",
                risk.riskScore ?? 0
            );


            // =============================================
            // 🔹 RISK FACTORS
            // =============================================
            const factorsContainer =
                document.getElementById(
                    "risk-factors"
                );


            if (factorsContainer) {

                factorsContainer.innerHTML = "";


                const factors =
                    Array.isArray(risk.factors)
                        ? risk.factors
                        : [];


                if (factors.length === 0) {

                    factorsContainer.innerHTML = `
                        <div class="p-4 text-gray-400">
                            No risk factors available.
                        </div>
                    `;

                } else {

                    factors.forEach(
                        factor => {

                            let color =
                                "yellow";


                            if (
                                factor.severity ===
                                "Critical"
                            ) {
                                color = "red";
                            }


                            else if (
                                factor.severity ===
                                "High"
                            ) {
                                color = "orange";
                            }


                            else if (
                                factor.severity ===
                                "Low"
                            ) {
                                color = "emerald";
                            }


                            /*
                             * Backend fields:
                             *
                             * title
                             * description
                             * severity
                             * score
                             */

                            const description =
                                factor.description ??
                                factor.desc ??
                                "";


                            const score =
                                Number(
                                    factor.score ??
                                    factor.value ??
                                    0
                                );


                            factorsContainer.innerHTML += `

                                <div class="
                                    flex items-center
                                    justify-between
                                    p-3
                                    bg-white/5
                                    rounded-lg
                                    mb-2
                                ">

                                    <div class="flex-1">

                                        <p class="
                                            text-sm
                                            text-gray-300
                                        ">
                                            ${factor.title ?? "Risk Factor"}
                                        </p>

                                        <p class="
                                            text-xs
                                            text-gray-500
                                            mt-1
                                        ">
                                            ${description}
                                        </p>

                                    </div>


                                    <div class="
                                        text-right
                                        ml-4
                                    ">

                                        <p class="
                                            text-sm
                                            font-semibold
                                            text-${color}-400
                                        ">
                                            ${factor.severity ?? "--"}
                                        </p>


                                        <div class="
                                            w-16
                                            h-1
                                            bg-white/10
                                            rounded-full
                                            mt-1
                                        ">

                                            <div
                                                class="
                                                    h-full
                                                    bg-${color}-500
                                                    rounded-full
                                                "
                                                style="
                                                    width:${Math.max(
                                                        0,
                                                        Math.min(
                                                            100,
                                                            score
                                                        )
                                                    )}%;
                                                "
                                            ></div>

                                        </div>

                                    </div>

                                </div>
                            `;
                        }
                    );
                }
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


                if (alerts.length === 0) {

                    alertsContainer.innerHTML = `
                        <div class="
                            p-3
                            bg-white/5
                            rounded
                            text-gray-400
                        ">
                            No active alerts.
                        </div>
                    `;

                } else {

                    alerts.forEach(
                        alert => {

                            let color =
                                "cyan";


                            if (
                                alert.type ===
                                "ALERT"
                            ) {
                                color = "red";
                            }


                            else if (
                                alert.type ===
                                "WARNING"
                            ) {
                                color = "yellow";
                            }


                            else if (
                                alert.type ===
                                "NOTICE"
                            ) {
                                color = "cyan";
                            }


                            alertsContainer.innerHTML += `

                                <div class="
                                    p-3
                                    border-l-4
                                    border-${color}-500
                                    bg-${color}-500/10
                                    rounded
                                    mb-2
                                ">

                                    <p class="
                                        text-xs
                                        text-${color}-400
                                        font-semibold
                                    ">
                                        ${alert.type ?? "NOTICE"}
                                    </p>


                                    <p class="
                                        text-sm
                                        text-gray-300
                                        mt-1
                                    ">
                                        ${alert.message ?? ""}
                                    </p>


                                    <p class="
                                        text-xs
                                        text-gray-500
                                        mt-1
                                    ">
                                        ${alert.time ?? ""}
                                    </p>

                                </div>
                            `;
                        }
                    );
                }
            }


            // =============================================
            // 🔹 LIVE MARINE DATA
            // =============================================
            const live =
                risk.liveData || {};


            setText(
                "risk-temperature",
                live.temperature !== undefined
                    ? `${Number(live.temperature).toFixed(2)} °C`
                    : "--"
            );


            setText(
                "risk-wave",
                live.waveHeight !== undefined
                    ? `${Number(live.waveHeight).toFixed(2)} m`
                    : "--"
            );


            setText(
                "risk-wind",
                live.windSpeed !== undefined
                    ? `${Number(live.windSpeed).toFixed(2)} km/h`
                    : "--"
            );


            setText(
                "risk-sea-level",
                live.seaLevel !== undefined
                    ? `${Number(live.seaLevel).toFixed(2)} m`
                    : "--"
            );


            setText(
                "risk-salinity",
                live.salinity !== undefined
                    ? `${Number(live.salinity).toFixed(2)} PSU`
                    : "--"
            );


            setText(
                "risk-current",
                live.currentVelocity !== undefined
                    ? `${Number(live.currentVelocity).toFixed(2)} m/s`
                    : "--"
            );


            setText(
                "risk-current-direction",
                live.currentDirection !== undefined
                    ? `${Number(live.currentDirection).toFixed(1)}°`
                    : "--"
            );


            console.log(
                "✅ Risk dashboard updated for:",
                risk.locationName
            );


        } catch (error) {

            console.error(
                "❌ Risk Error:",
                error
            );


            // Do NOT destroy existing dashboard
            // just show an error if the element exists.

            const errorElement =
                document.getElementById(
                    "risk-error"
                );


            if (errorElement) {

                errorElement.innerText =
                    "Unable to load risk data";

                errorElement.classList.remove(
                    "hidden"
                );
            }
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
        60000
    );


    // =============================================
    // 🔹 REFRESH WHEN PORT CHANGES
    // =============================================
    document.addEventListener(
        "portChanged",
        () => {

            console.log(
                "🔄 Port changed - refreshing risk data"
            );

            loadRiskData();
        }
    );


    // Also listen for common select changes
    const possibleSelectors = [
        "#port-select",
        "#location-select",
        "#portSelector",
        "#locationSelector"
    ];


    possibleSelectors.forEach(
        selector => {

            const element =
                document.querySelector(
                    selector
                );


            if (element) {

                element.addEventListener(
                    "change",
                    () => {

                        const location =
                            element.value
                                .toLowerCase()
                                .trim();

                        window.selectedLocation =
                            location;

                        localStorage.setItem(
                            "selectedLocation",
                            location
                        );

                        loadRiskData();
                    }
                );
            }
        }
    );

});
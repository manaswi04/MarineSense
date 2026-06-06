// =============================================
// 📢 Marine Advisory Engine
// =============================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

    async function loadAdvisories() {

        try {

            const res = await fetch(
                "http://127.0.0.1:8000/api/advisory"
            );

            if (!res.ok) {

                throw new Error(
                    "Failed to fetch advisories"
                );
            }

            const data = await res.json();

            console.log(
                "📢 Advisory API:",
                data
            );

            // =============================================
            // 🔹 SUMMARY
            // =============================================
            const summary =
                data.summary;

            document.getElementById(
                "adv-risk-score"
            ).innerText =
                summary.riskScore;

            document.getElementById(
                "adv-wave"
            ).innerText =
                summary.waveHeight.toFixed(2) + " m";

            document.getElementById(
                "adv-oxygen"
            ).innerText =
                summary.oxygen.toFixed(2) + " mg/L";

            document.getElementById(
                "adv-temp"
            ).innerText =
                summary.temperature.toFixed(2) + " °C";

            document.getElementById(
                "adv-sea"
            ).innerText =
                summary.seaLevel.toFixed(2) + " m";

            // =============================================
            // 🔹 ADVISORY CARDS
            // =============================================
            const container =
                document.getElementById(
                    "advisory-cards"
                );

            container.innerHTML = "";

            data.advisories.forEach(
                advisory => {

                let color =
                    "cyan";

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
                            flex justify-between
                            items-start mb-4
                        ">

                            <div>

                                <p class="
                                    text-xs
                                    uppercase
                                    text-${color}-400
                                    mb-2
                                ">
                                    ${advisory.type}
                                </p>

                                <h3 class="
                                    text-xl
                                    font-bold
                                    text-white
                                ">
                                    ${advisory.title}
                                </h3>

                            </div>

                            <span class="
                                px-3 py-1
                                rounded-full
                                bg-${color}-500/20
                                text-${color}-400
                                text-xs
                            ">
                                ${advisory.severity}
                            </span>

                        </div>

                        <p class="
                            text-gray-300
                            mb-4
                        ">
                            ${advisory.message}
                        </p>

                        <div class="
                            p-3 rounded-xl
                            bg-white/5
                        ">

                            <p class="
                                text-xs text-gray-500
                                mb-1
                            ">
                                Recommendation
                            </p>

                            <p class="
                                text-sm text-cyan-300
                            ">
                                ${advisory.recommendation}
                            </p>

                        </div>

                    </div>
                `;
            });

        } catch (error) {

            console.error(
                "❌ Advisory Error:",
                error
            );
        }
    }

    // =============================================
    // 🔹 INITIAL LOAD
    // =============================================
    loadAdvisories();

    // =============================================
    // 🔹 AUTO REFRESH
    // =============================================
    setInterval(
        loadAdvisories,
        20000
    );
});

// =============================================
// 🔹 DOWNLOAD REPORT
// =============================================
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
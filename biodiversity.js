// =============================================
// 🌊 MarineSense Biodiversity Module
// =============================================

document.addEventListener("DOMContentLoaded", () => {

    // =============================================
    // 🔹 CHART VARIABLES
    // =============================================
    let biodiversityChart;
    let speciesChart;

    // =============================================
    // 🔹 LOAD BIODIVERSITY DATA
    // =============================================
    async function loadBiodiversityData() {

        try {

            // =============================================
            // 🔹 API CALL
            // =============================================
            const res = await fetch(
                "http://127.0.0.1:8000/api/biodiversity"
            );

            if (!res.ok) {
                throw new Error(
                    "Failed to fetch biodiversity data"
                );
            }

            const result = await res.json();

            console.log(
                "🌿 Biodiversity API:",
                result
            );

            // =============================================
            // 🔹 SAFETY CHECK
            // =============================================
            if (
                result.status !== "success"
            ) {

                throw new Error(
                    result.message ||
                    "Invalid biodiversity response"
                );
            }

            const beaches =
                result.data || [];

            // =============================================
            // 🔹 TOP METRICS
            // =============================================
            const totalBeaches =
                beaches.length;

            const totalSpecies =
                result.totalSpecies || 0;

            const avgScore =
                beaches.length > 0
                ?
                (
                    beaches.reduce(
                        (acc, beach) =>
                            acc + beach.biodiversityScore,
                        0
                    ) / beaches.length
                ).toFixed(1)
                :
                0;

            // =============================================
            // 🔹 UPDATE METRICS UI
            // =============================================
            const beachesEl =
                document.getElementById(
                    "total-beaches"
                );

            const speciesEl =
                document.getElementById(
                    "total-species"
                );

            const avgScoreEl =
                document.getElementById(
                    "avg-score"
                );

            if (beachesEl) {
                beachesEl.innerText =
                    totalBeaches;
            }

            if (speciesEl) {
                speciesEl.innerText =
                    totalSpecies;
            }

            if (avgScoreEl) {
                avgScoreEl.innerText =
                    avgScore;
            }

            // =============================================
            // 🔹 BEACH CARDS
            // =============================================
            const container =
                document.getElementById(
                    "beach-cards"
                );

            if (container) {

                container.innerHTML = "";

                beaches.forEach(beach => {

                    let riskColor =
                        "emerald";

                    if (
                        beach.riskLevel === "Medium"
                    ) {
                        riskColor = "yellow";
                    }

                    if (
                        beach.riskLevel === "High"
                    ) {
                        riskColor = "red";
                    }

                    container.innerHTML += `

                        <div class="
                            glass-effect
                            rounded-2xl
                            p-5
                            border
                            border-${riskColor}-500/20
                        ">

                            <!-- Header -->
                            <div class="
                                flex justify-between
                                items-start mb-4
                            ">

                                <div>

                                    <h3 class="
                                        text-lg
                                        font-bold
                                        text-white
                                    ">
                                        ${beach.beach}
                                    </h3>

                                    <p class="
                                        text-gray-400
                                        text-sm mt-1
                                    ">
                                        Mumbai Coastal Region
                                    </p>

                                </div>

                                <span class="
                                    px-3 py-1
                                    rounded-full
                                    text-xs
                                    bg-${riskColor}-500/20
                                    text-${riskColor}-400
                                ">
                                    ${beach.riskLevel}
                                </span>

                            </div>

                            <!-- Biodiversity Score -->
                            <div class="mb-4">

                                <div class="
                                    flex justify-between
                                    text-sm mb-2
                                ">

                                    <span class="
                                        text-gray-400
                                    ">
                                        Biodiversity Score
                                    </span>

                                    <span class="
                                        text-cyan-400
                                    ">
                                        ${beach.biodiversityScore}
                                    </span>

                                </div>

                                <div class="
                                    w-full h-2
                                    bg-white/5
                                    rounded-full
                                ">

                                    <div
                                        class="
                                            h-2 rounded-full
                                            bg-cyan-400
                                        "

                                        style="
                                            width:
                                            ${beach.biodiversityScore}%
                                        "
                                    ></div>

                                </div>

                            </div>

                            <!-- Species Tags -->
                            <div class="
                                flex flex-wrap gap-2
                            ">

                                ${beach.species.map(species => `

                                    <span class="
                                        px-2 py-1
                                        rounded-lg
                                        bg-white/5
                                        text-xs
                                        text-gray-300
                                    ">
                                        ${species}
                                    </span>

                                `).join("")}

                            </div>

                        </div>
                    `;
                });
            }

            // =============================================
            // 🔹 CHART DATA
            // =============================================
            const labels =
                beaches.map(
                    beach => beach.beach
                );

            const scores =
                beaches.map(
                    beach =>
                    beach.biodiversityScore
                );

            const speciesCounts =
                beaches.map(
                    beach =>
                    beach.species.length
                );

            // =============================================
            // 🔹 BIODIVERSITY BAR CHART
            // =============================================
            if (biodiversityChart) {
                biodiversityChart.destroy();
            }

            biodiversityChart =
                new Chart(

                    document.getElementById(
                        "biodiversityChart"
                    ),

                    {
                        type: "bar",

                        data: {

                            labels,

                            datasets: [{

                                label:
                                    "Biodiversity Score",

                                data: scores,

                                backgroundColor:
                                    "rgba(34,211,238,0.6)",

                                borderRadius: 10
                            }]
                        },

                        options: {

                            responsive: true,

                            maintainAspectRatio: false,

                            plugins: {

                                legend: {
                                    display: false
                                }
                            },

                            scales: {

                                x: {
                                    ticks: {
                                        color: "#9ca3af"
                                    },

                                    grid: {
                                        display: false
                                    }
                                },

                                y: {

                                    beginAtZero: true,

                                    ticks: {
                                        color: "#9ca3af"
                                    },

                                    grid: {
                                        color:
                                        "rgba(255,255,255,0.05)"
                                    }
                                }
                            }
                        }
                    }
                );

            // =============================================
            // 🔹 SPECIES DOUGHNUT CHART
            // =============================================
            if (speciesChart) {
                speciesChart.destroy();
            }

            speciesChart =
                new Chart(

                    document.getElementById(
                        "speciesChart"
                    ),

                    {
                        type: "doughnut",

                        data: {

                            labels,

                            datasets: [{

                                data: speciesCounts,

                                backgroundColor: [

                                    "#22d3ee",
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

        } catch (error) {

            console.error(
                "❌ Biodiversity Error:",
                error
            );

            const container =
                document.getElementById(
                    "beach-cards"
                );

            if (container) {

                container.innerHTML = `

                    <div class="
                        col-span-full
                        glass-effect
                        rounded-2xl
                        p-8
                        text-center
                    ">

                        <h3 class="
                            text-xl font-bold
                            text-red-400 mb-2
                        ">
                            Failed to Load Biodiversity Data
                        </h3>

                        <p class="text-gray-400">
                            Check backend API connection
                        </p>

                    </div>
                `;
            }
        }
    }

    // =============================================
    // 🔹 INITIAL LOAD
    // =============================================
    loadBiodiversityData();

    // =============================================
    // 🔹 AUTO REFRESH
    // =============================================
    setInterval(
        loadBiodiversityData,
        60000
    );
});
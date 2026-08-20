// =============================================
// 🌊 MarineSense Biodiversity Module
// =============================================

document.addEventListener("DOMContentLoaded", () => {

    // =============================================
    // 🔹 CHART VARIABLES
    // =============================================

    let biodiversityChart = null;
    let speciesChart = null;


    // =============================================
    // 🔹 GET SELECTED LOCATION
    // =============================================

    function getSelectedLocation() {

        let location =
            localStorage.getItem("selectedLocation");

        // If your dashboard stores another key,
        // this fallback keeps Mumbai as default.
        if (!location) {
            location = "mumbai";
        }

        return location
            .toLowerCase()
            .trim();
    }


    // =============================================
    // 🔹 LOAD BIODIVERSITY DATA
    // =============================================

    async function loadBiodiversityData() {

        try {

            // =============================================
            // GET LOCATION
            // =============================================

            const selectedLocation =
                getSelectedLocation();

            console.log(
                "🌿 Biodiversity selected location:",
                selectedLocation
            );


            // =============================================
            // API URL
            // IMPORTANT:
            // BACKTICKS ARE REQUIRED
            // =============================================

            const apiUrl =
                `http://127.0.0.1:8000/api/biodiversity?location=${encodeURIComponent(selectedLocation)}`;

            console.log(
                "📡 Biodiversity API:",
                apiUrl
            );


            // =============================================
            // API CALL
            // =============================================

            const res = await fetch(
                apiUrl,
                {
                    cache: "no-store"
                }
            );


            if (!res.ok) {

                throw new Error(
                    `Biodiversity API returned ${res.status}`
                );
            }


            const result =
                await res.json();


            console.log(
                "🌿 Biodiversity API response:",
                result
            );


            // =============================================
            // SAFETY CHECK
            // =============================================

            if (
                result.status &&
                result.status !== "success"
            ) {

                throw new Error(
                    result.message ||
                    "Invalid biodiversity response"
                );
            }


            // =============================================
            // EXTRACT DATA
            //
            // Supports:
            // result.data
            // result.beaches
            // result.species
            // =============================================

            let beaches = [];

            if (Array.isArray(result.data)) {

                beaches = result.data;

            } else if (
                Array.isArray(result.beaches)
            ) {

                beaches = result.beaches;

            } else if (
                Array.isArray(result.biodiversity)
            ) {

                beaches =
                    result.biodiversity;
            }


            console.log(
                "🌊 Biodiversity records:",
                beaches
            );


            // =============================================
            // TOP METRICS
            // =============================================

            const totalBeaches =
                beaches.length;


            let totalSpecies = 0;


            // =============================================
            // CALCULATE SPECIES COUNT
            // =============================================

            beaches.forEach(beach => {

                const species =
                    Array.isArray(beach.species)
                        ? beach.species
                        : [];

                totalSpecies +=
                    species.length;
            });


            // If backend already gives totalSpecies,
            // prefer that value.

            if (
                typeof result.totalSpecies ===
                "number"
            ) {

                totalSpecies =
                    result.totalSpecies;
            }


            // =============================================
            // BIODIVERSITY SCORE
            // =============================================

            let avgScore = 0;


            if (beaches.length > 0) {

                const scores =
                    beaches.map(beach => {

                        const score =
                            Number(
                                beach.biodiversityScore ??
                                beach.biodiversity_score ??
                                beach.score ??
                                0
                            );

                        return isNaN(score)
                            ? 0
                            : score;
                    });


                const totalScore =
                    scores.reduce(
                        (sum, score) =>
                            sum + score,
                        0
                    );


                avgScore =
                    (
                        totalScore /
                        beaches.length
                    ).toFixed(1);
            }


            // =============================================
            // UPDATE TOP METRICS
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
            // LOCATION NAME
            // =============================================

            const locationEl =
                document.getElementById(
                    "biodiversity-location"
                );


            if (locationEl) {

                locationEl.innerText =
                    result.locationName ||
                    selectedLocation;
            }


            // =============================================
            // BEACH CARDS
            // =============================================

            const container =
                document.getElementById(
                    "beach-cards"
                );


            if (container) {

                container.innerHTML = "";


                // =============================================
                // NO DATA
                // =============================================

                if (beaches.length === 0) {

                    container.innerHTML = `

                        <div class="
                            col-span-full
                            glass-effect
                            rounded-2xl
                            p-8
                            text-center
                            border
                            border-cyan-500/20
                        ">

                            <h3 class="
                                text-xl
                                font-bold
                                text-white
                                mb-2
                            ">
                                No Biodiversity Data
                            </h3>

                            <p class="
                                text-gray-400
                            ">
                                No biodiversity records
                                are currently available
                                for ${selectedLocation}.
                            </p>

                        </div>

                    `;

                } else {


                    // =============================================
                    // CREATE BEACH CARDS
                    // =============================================

                    beaches.forEach(beach => {

                        // -----------------------------
                        // SAFE VALUES
                        // -----------------------------

                        const beachName =
                            beach.beach ||
                            beach.name ||
                            beach.location ||
                            "Marine Zone";


                        const riskLevel =
                            beach.riskLevel ||
                            beach.risk ||
                            "Low";


                        const biodiversityScore =
                            Number(
                                beach.biodiversityScore ??
                                beach.biodiversity_score ??
                                beach.score ??
                                0
                            );


                        const species =
                            Array.isArray(
                                beach.species
                            )
                                ? beach.species
                                : [];


                        // -----------------------------
                        // RISK COLOR
                        // -----------------------------

                        let riskColor =
                            "emerald";


                        if (
                            riskLevel === "Medium"
                        ) {

                            riskColor =
                                "yellow";
                        }


                        if (
                            riskLevel === "High"
                        ) {

                            riskColor =
                                "red";
                        }


                        if (
                            riskLevel === "Critical"
                        ) {

                            riskColor =
                                "red";
                        }


                        // -----------------------------
                        // SPECIES HTML
                        // -----------------------------

                        let speciesHTML = "";


                        if (
                            species.length > 0
                        ) {

                            speciesHTML =
                                species.map(
                                    item => `

                                    <span class="
                                        px-2
                                        py-1
                                        rounded-lg
                                        bg-white/5
                                        text-xs
                                        text-gray-300
                                    ">
                                        ${item}
                                    </span>

                                `
                                ).join("");

                        } else {

                            speciesHTML = `

                                <span class="
                                    text-xs
                                    text-gray-500
                                ">
                                    Species data unavailable
                                </span>

                            `;
                        }


                        // -----------------------------
                        // CARD
                        // -----------------------------

                        container.innerHTML += `

                            <div class="
                                glass-effect
                                rounded-2xl
                                p-5
                                border
                                border-${riskColor}-500/20
                            ">

                                <div class="
                                    flex
                                    justify-between
                                    items-start
                                    mb-4
                                ">

                                    <div>

                                        <h3 class="
                                            text-lg
                                            font-bold
                                            text-white
                                        ">
                                            ${beachName}
                                        </h3>

                                        <p class="
                                            text-gray-400
                                            text-sm
                                            mt-1
                                        ">
                                            ${result.locationName || selectedLocation}
                                        </p>

                                    </div>


                                    <span class="
                                        px-3
                                        py-1
                                        rounded-full
                                        text-xs
                                        bg-${riskColor}-500/20
                                        text-${riskColor}-400
                                    ">
                                        ${riskLevel}
                                    </span>

                                </div>


                                <!-- Biodiversity Score -->

                                <div class="mb-4">

                                    <div class="
                                        flex
                                        justify-between
                                        text-sm
                                        mb-2
                                    ">

                                        <span class="
                                            text-gray-400
                                        ">
                                            Biodiversity Score
                                        </span>


                                        <span class="
                                            text-cyan-400
                                        ">
                                            ${biodiversityScore}
                                        </span>

                                    </div>


                                    <div class="
                                        w-full
                                        h-2
                                        bg-white/5
                                        rounded-full
                                    ">

                                        <div
                                            class="
                                                h-2
                                                rounded-full
                                                bg-cyan-400
                                            "
                                            style="
                                                width:
                                                ${Math.max(
                                                    0,
                                                    Math.min(
                                                        biodiversityScore,
                                                        100
                                                    )
                                                )}%
                                            "
                                        ></div>

                                    </div>

                                </div>


                                <!-- Species -->

                                <div class="
                                    flex
                                    flex-wrap
                                    gap-2
                                ">

                                    ${speciesHTML}

                                </div>

                            </div>

                        `;
                    });
                }
            }


            // =============================================
            // CHART DATA
            // =============================================

            const labels =
                beaches.map(
                    beach =>
                        beach.beach ||
                        beach.name ||
                        beach.location ||
                        "Marine Zone"
                );


            const scores =
                beaches.map(
                    beach =>
                        Number(
                            beach.biodiversityScore ??
                            beach.biodiversity_score ??
                            beach.score ??
                            0
                        )
                );


            const speciesCounts =
                beaches.map(
                    beach =>
                        Array.isArray(
                            beach.species
                        )
                            ? beach.species.length
                            : 0
                );


            // =============================================
            // BIODIVERSITY BAR CHART
            // =============================================

            const biodiversityCanvas =
                document.getElementById(
                    "biodiversityChart"
                );


            if (
                biodiversityCanvas &&
                typeof Chart !== "undefined"
            ) {

                if (biodiversityChart) {

                    biodiversityChart.destroy();
                }


                biodiversityChart =
                    new Chart(
                        biodiversityCanvas,
                        {

                            type: "bar",

                            data: {

                                labels: labels,

                                datasets: [{

                                    label:
                                        "Biodiversity Score",

                                    data:
                                        scores,

                                    backgroundColor:
                                        "rgba(34,211,238,0.6)",

                                    borderRadius:
                                        10

                                }]
                            },


                            options: {

                                responsive:
                                    true,

                                maintainAspectRatio:
                                    false,

                                plugins: {

                                    legend: {

                                        display:
                                            false
                                    }
                                },


                                scales: {

                                    x: {

                                        ticks: {

                                            color:
                                                "#9ca3af"
                                        },

                                        grid: {

                                            display:
                                                false
                                        }
                                    },


                                    y: {

                                        beginAtZero:
                                            true,

                                        max:
                                            100,

                                        ticks: {

                                            color:
                                                "#9ca3af"
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
            }


            // =============================================
            // SPECIES DOUGHNUT CHART
            // =============================================

            const speciesCanvas =
                document.getElementById(
                    "speciesChart"
                );


            if (
                speciesCanvas &&
                typeof Chart !== "undefined"
            ) {

                if (speciesChart) {

                    speciesChart.destroy();
                }


                speciesChart =
                    new Chart(
                        speciesCanvas,
                        {

                            type:
                                "doughnut",

                            data: {

                                labels:
                                    labels,

                                datasets: [{

                                    data:
                                        speciesCounts,

                                    backgroundColor: [

                                        "#22d3ee",
                                        "#10b981",
                                        "#fbbf24",
                                        "#ef4444",
                                        "#8b5cf6",
                                        "#3b82f6"

                                    ],

                                    borderWidth:
                                        0

                                }]
                            },


                            options: {

                                responsive:
                                    true,

                                maintainAspectRatio:
                                    false,

                                plugins: {

                                    legend: {

                                        labels: {

                                            color:
                                                "#9ca3af"
                                        }
                                    }
                                }
                            }
                        }
                    );
            }


            console.log(
                "✅ Biodiversity dashboard updated for:",
                result.locationName ||
                selectedLocation
            );

        } catch (error) {

            console.error(
                "❌ Biodiversity Error:",
                error
            );


            // =============================================
            // SHOW ERROR
            // =============================================

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
                        border
                        border-red-500/20
                    ">

                        <h3 class="
                            text-xl
                            font-bold
                            text-red-400
                            mb-2
                        ">
                            Failed to Load Biodiversity Data
                        </h3>

                        <p class="
                            text-gray-400
                            mb-2
                        ">
                            ${error.message}
                        </p>

                        <p class="
                            text-gray-500
                            text-sm
                        ">
                            Check the backend API
                            and browser console.
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
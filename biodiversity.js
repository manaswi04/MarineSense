// =============================================
// MarineSense Biodiversity Module
// =============================================

document.addEventListener("DOMContentLoaded", () => {

    let biodiversityChart = null;
    let speciesChart = null;

    // Prevent overlapping requests
    let biodiversityRequestInProgress = false;

    // =============================================
    // GET SELECTED LOCATION
    // =============================================

    function getSelectedLocation() {
        let location = window.selectedLocation;

        if (!location) {
            location = localStorage.getItem("selectedLocation");
        }

        if (!location) {
            location = "mumbai";
        }

        return String(location).toLowerCase().trim();
    }

    // =============================================
    // LOAD BIODIVERSITY DATA
    // =============================================

    async function loadBiodiversityData() {

        if (biodiversityRequestInProgress) {
            return;
        }

        biodiversityRequestInProgress = true;

        let biodiversityTimeoutId;

        try {

            const selectedLocation = getSelectedLocation();

            console.log(
                "Biodiversity selected location:",
                selectedLocation
            );

            const apiUrl =
                `http://127.0.0.1:8000/api/biodiversity?location=${encodeURIComponent(selectedLocation)}`;

            console.log("Biodiversity API:", apiUrl);

            // Abort a request if it takes longer than 30 seconds
            const controller = new AbortController();

            biodiversityTimeoutId = setTimeout(() => {
                controller.abort();
            }, 30000);

            const res = await fetch(apiUrl, {
                cache: "no-store",
                signal: controller.signal
            });

            if (!res.ok) {
                throw new Error(
                    `Biodiversity API returned ${res.status}`
                );
            }

            const result = await res.json();

            console.log("Biodiversity API response:", result);

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
            // EXTRACT BIODIVERSITY DATA
            // =============================================

            let beaches = [];

            if (Array.isArray(result.data)) {
                beaches = result.data;
            } else if (Array.isArray(result.beaches)) {
                beaches = result.beaches;
            } else if (Array.isArray(result.biodiversity)) {
                beaches = result.biodiversity;
            }

            console.log("Biodiversity records:", beaches);

            // =============================================
            // TOP METRICS
            // =============================================

            const totalBeaches = beaches.length;

            let totalSpecies = 0;

            beaches.forEach(beach => {
                const species = Array.isArray(beach.species)
                    ? beach.species
                    : [];

                totalSpecies += species.length;
            });

            if (typeof result.totalSpecies === "number") {
                totalSpecies = result.totalSpecies;
            }

            // =============================================
            // AVERAGE BIODIVERSITY SCORE
            // =============================================

            let avgScore = 0;

            if (beaches.length > 0) {

                const scores = beaches.map(beach => {
                    const score = Number(
                        beach.biodiversityScore ??
                        beach.biodiversity_score ??
                        beach.score ??
                        0
                    );

                    return Number.isFinite(score) ? score : 0;
                });

                const totalScore = scores.reduce(
                    (sum, score) => sum + score,
                    0
                );

                avgScore = (
                    totalScore / beaches.length
                ).toFixed(1);
            }

            // =============================================
            // UPDATE TOP METRICS
            // =============================================

            const beachesEl =
                document.getElementById("total-beaches");

            const speciesEl =
                document.getElementById("total-species");

            const avgScoreEl =
                document.getElementById("avg-score");

            if (beachesEl) {
                beachesEl.innerText = totalBeaches;
            }

            if (speciesEl) {
                speciesEl.innerText = totalSpecies;
            }

            if (avgScoreEl) {
                avgScoreEl.innerText = avgScore;
            }

            // =============================================
            // LOCATION NAME
            // =============================================

            const locationName =
                result.locationName ||
                result.location ||
                selectedLocation;

            const locationEl =
                document.getElementById("biodiversity-location");

            if (locationEl) {
                locationEl.innerText = locationName;
            }

            // =============================================
            // BIODIVERSITY CARDS
            // =============================================

            const container =
                document.getElementById("beach-cards");

            if (container) {

                container.innerHTML = "";

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

                            <p class="text-gray-400">
                                No biodiversity records are
                                currently available for
                                ${selectedLocation}.
                            </p>
                        </div>
                    `;

                } else {

                    beaches.forEach(beach => {

                        const beachName =
                            beach.beach ||
                            beach.name ||
                            beach.location ||
                            "Marine Zone";

                        const riskLevel =
                            beach.riskLevel ||
                            beach.risk ||
                            "Low";

                        const biodiversityScore = Number(
                            beach.biodiversityScore ??
                            beach.biodiversity_score ??
                            beach.score ??
                            0
                        );

                        const safeScore = Number.isFinite(
                            biodiversityScore
                        )
                            ? Math.max(
                                0,
                                Math.min(100, biodiversityScore)
                            )
                            : 0;

                        const species = Array.isArray(
                            beach.species
                        )
                            ? beach.species
                            : [];

                        // Risk color
                        let riskColor = "emerald";

                        if (riskLevel === "Medium") {
                            riskColor = "yellow";
                        } else if (
                            riskLevel === "High" ||
                            riskLevel === "Critical"
                        ) {
                            riskColor = "red";
                        }

                        // Species labels
                        const speciesHTML = species.length > 0
                            ? species.map(item => `
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
                            `).join("")
                            : `
                                <span class="
                                    text-xs
                                    text-gray-500
                                ">
                                    Species data unavailable
                                </span>
                            `;

                        // Render card
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
                                            ${locationName}
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

                                <div class="mb-4">

                                    <div class="
                                        flex
                                        justify-between
                                        text-sm
                                        mb-2
                                    ">
                                        <span class="text-gray-400">
                                            Biodiversity Score
                                        </span>

                                        <span class="text-cyan-400">
                                            ${safeScore}
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
                                            style="width:${safeScore}%"
                                        ></div>
                                    </div>

                                </div>

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

            const labels = beaches.map(beach =>
                beach.beach ||
                beach.name ||
                beach.location ||
                "Marine Zone"
            );

            const scores = beaches.map(beach => {
                const score = Number(
                    beach.biodiversityScore ??
                    beach.biodiversity_score ??
                    beach.score ??
                    0
                );

                return Number.isFinite(score) ? score : 0;
            });

            const speciesCounts = beaches.map(beach =>
                Array.isArray(beach.species)
                    ? beach.species.length
                    : 0
            );

            // =============================================
            // BIODIVERSITY BAR CHART
            // =============================================

            const biodiversityCanvas =
                document.getElementById("biodiversityChart");

            if (
                biodiversityCanvas &&
                typeof Chart !== "undefined"
            ) {

                if (biodiversityChart) {
                    biodiversityChart.destroy();
                }

                biodiversityChart = new Chart(
                    biodiversityCanvas,
                    {
                        type: "bar",

                        data: {
                            labels: labels,

                            datasets: [{
                                label: "Biodiversity Score",
                                data: scores,
                                backgroundColor: "rgba(34,211,238,0.6)",
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
                                    max: 100,

                                    ticks: {
                                        color: "#9ca3af"
                                    },

                                    grid: {
                                        color: "rgba(255,255,255,0.05)"
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
                document.getElementById("speciesChart");

            if (
                speciesCanvas &&
                typeof Chart !== "undefined"
            ) {

                if (speciesChart) {
                    speciesChart.destroy();
                }

                speciesChart = new Chart(
                    speciesCanvas,
                    {
                        type: "doughnut",

                        data: {
                            labels: labels,

                            datasets: [{
                                data: speciesCounts,

                                backgroundColor: [
                                    "#22d3ee",
                                    "#10b981",
                                    "#fbbf24",
                                    "#ef4444",
                                    "#8b5cf6",
                                    "#3b82f6"
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
            }

            console.log(
                "Biodiversity dashboard updated for:",
                locationName
            );

            // Hide previous error message on success
            const errorElement =
                document.getElementById("biodiversity-error");

            if (errorElement) {
                errorElement.classList.add("hidden");
                errorElement.innerText = "";
            }

        } catch (error) {

            console.error("Biodiversity Error:", error);

            const container =
                document.getElementById("beach-cards");

            if (container) {

                const errorMessage =
                    error.name === "AbortError"
                        ? "The biodiversity request timed out after 30 seconds."
                        : error.message;

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
                            ${errorMessage}
                        </p>

                        <p class="
                            text-gray-500
                            text-sm
                        ">
                            Check the backend API and browser console.
                        </p>
                    </div>
                `;
            }

        } finally {

            // Always release the request lock
            if (biodiversityTimeoutId) {
                clearTimeout(biodiversityTimeoutId);
            }

            biodiversityRequestInProgress = false;
        }
    }

    // =============================================
    // INITIAL LOAD
    // =============================================

    loadBiodiversityData();

    // =============================================
    // AUTO REFRESH EVERY 60 SECONDS
    // =============================================

    setInterval(
        loadBiodiversityData,
        60000
    );

    // =============================================
    // REFRESH WHEN LOCATION CHANGES
    // =============================================

    document.addEventListener("portChanged", () => {
        loadBiodiversityData();
    });

});
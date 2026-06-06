console.log("✅ datasource.js loaded");

// =============================================
// 🔹 LOAD DATA SOURCES
// =============================================
function loadDataSources() {

    console.log("📚 Loading Data Sources...");

    const container =
        document.getElementById(
            "datasource-content"
        );

    if (!container) {

        console.error(
            "❌ datasource-content not found"
        );

        return;
    }

    const locationSelect =
        document.getElementById(
            "location-select"
        );

    const location =
        locationSelect
            ? locationSelect.value.toLowerCase()
            : "mumbai";

    // =====================================
    // 🔹 ONLY MUMBAI SUPPORTED
    // =====================================
    if (location !== "mumbai") {

        container.innerHTML = `

            <div class="
                col-span-full
                glass-effect
                rounded-3xl
                p-10
                text-center
            ">

                <h2 class="
                    text-3xl
                    font-bold
                    text-red-400
                ">
                    Mumbai Port Only
                </h2>

                <p class="
                    text-gray-400
                    mt-4
                ">
                    Data Sources are currently
                    available only for Mumbai Port.
                </p>

            </div>

        `;

        return;
    }

    // =====================================
    // 🔹 SOURCE DATA
    // =====================================
    const sources = [

        {
            icon: "🌊",
            title: "Copernicus Marine",
            data: "Sea Level, Salinity",
            description:
                "Provides oceanographic datasets used for marine analytics.",
            url:
                "https://marine.copernicus.eu"
        },

        {
            icon: "🌡️",
            title: "Open-Meteo Marine",
            data:
                "Temperature, Wind, Waves",
            description:
                "Real-time marine weather observations.",
            url:
                "https://open-meteo.com"
        },

        {
            icon: "🐠",
            title: "OBIS",
            data:
                "Marine Biodiversity",
            description:
                "Global marine species database.",
            url:
                "https://obis.org"
        },

        {
            icon: "⚓",
            title:
                "Mumbai Port Authority",
            data:
                "Port Information",
            description:
                "Official Mumbai Port information.",
            url:
                "https://mumbaiport.gov.in"
        },

        {
            icon: "🇮🇳",
            title: "INCOIS",
            data:
                "Ocean Intelligence",
            description:
                "Indian Ocean monitoring and forecasting.",
            url:
                "https://incois.gov.in"
        }
    ];

    // =====================================
    // 🔹 RENDER CARDS
    // =====================================
    container.innerHTML = "";

    sources.forEach(source => {

        container.innerHTML += `

            <div class="
                glass-effect
                rounded-3xl
                p-6
                border
                border-white/10
            ">

                <div class="
                    text-5xl
                    mb-4
                ">
                    ${source.icon}
                </div>

                <h3 class="
                    text-xl
                    font-bold
                    text-white
                ">
                    ${source.title}
                </h3>

                <p class="
                    text-cyan-400
                    mt-2
                    text-sm
                ">
                    ${source.data}
                </p>

                <p class="
                    text-gray-400
                    mt-4
                ">
                    ${source.description}
                </p>

                <a
                    href="${source.url}"
                    target="_blank"
                    class="
                        inline-block
                        mt-4
                        text-cyan-400
                    "
                >
                    Visit Source →
                </a>

            </div>
        `;
    });

    console.log(
        "✅ Data Sources Loaded"
    );
}
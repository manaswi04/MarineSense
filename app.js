/* =============================================
   MarineSense – UI Logic Only
 /* =============================================
   MarineSense – UI Logic Only
============================================= */

// =====================================
// 🔹 NAVIGATION
// =====================================
function navigateToPage(pageName) {

    console.log(
        "Opening Page:",
        pageName
    );

    // Remove active state
    document
        .querySelectorAll(".nav-link")
        .forEach(item => {

            item.classList.remove(
                "active"
            );
        });

    // Add active state
    const navLink =
        document.querySelector(
            `[data-page="${pageName}"]`
        );

    if (navLink) {

        navLink.classList.add(
            "active"
        );
    }

    // Hide all pages
    document
        .querySelectorAll(
            ".page-content"
        )
        .forEach(page => {

            page.classList.add(
                "hidden"
            );
        });

    // Show selected page
    const pageElement =
        document.getElementById(
            `${pageName}-page`
        );

    console.log(
        "Found Page:",
        pageElement
    );

    if (pageElement) {

        pageElement.classList.remove(
            "hidden"
        );

        console.log(
            "Page Opened Successfully"
        );
    }

    else {

        console.error(
            `❌ Missing page:
            ${pageName}-page`
        );
    }

    // =====================================
    // 🔹 PAGE TITLE
    // =====================================
    const titles = {

        dashboard:
            "Ocean Analytics Dashboard",

        biodiversity:
            "Biodiversity Insights",

        risk:
            "Risk Analysis",

        advisory:
            "Advisory Reports",

        datasources:
            "Data Sources"
    };

    const pageTitle =
        document.getElementById(
            "page-title"
        );

    if (pageTitle) {

        pageTitle.innerText =
            titles[pageName]
            || "MarineSense";
    }

    // =====================================
    // 🔹 LOAD DATA SOURCES
    // =====================================
    if (
        pageName ===
        "datasources"
    ) {

        if (
            typeof loadDataSources
            === "function"
        ) {

            loadDataSources();
        }

        else {

            console.error(
                "❌ datasource.js not loaded"
            );
        }
    }
}

// =====================================
// 🔹 NAV CLICK EVENTS
// =====================================
document
    .querySelectorAll(".nav-link")
    .forEach(item => {

        item.addEventListener(
            "click",
            function (e) {

                e.preventDefault();

                const pageName =
                    this.dataset.page;

                console.log(
                    "Clicked:",
                    pageName
                );

                navigateToPage(
                    pageName
                );
            }
        );
    });

// =====================================
// 🔹 DEFAULT PAGE
// =====================================
document.addEventListener(
    "DOMContentLoaded",
    () => {

        navigateToPage(
            "dashboard"
        );
    }
);

// =====================================
// 🔹 SEARCH DATABASE
// =====================================
const searchDatabase = [

    {
        title: "Temperature Dashboard",
        page: "dashboard",
        category: "Analytics",
        desc: "Live Mumbai port temperature"
    },

    {
        title: "Salinity Analysis",
        page: "dashboard",
        category: "Marine",
        desc: "Real salinity trends"
    },

    {
        title: "Risk Analysis",
        page: "risk",
        category: "AI",
        desc: "Marine risk prediction"
    },

    {
        title: "Sea Advisory Zones",
        page: "advisory",
        category: "Safety",
        desc: "Port entry guidance"
    },

    {
        title: "Biodiversity Insights",
        page: "biodiversity",
        category: "Research",
        desc: "Marine ecosystem tracking"
    },

    {
        title: "Data Sources",
        page: "datasources",
        category: "System",
        desc: "Connected APIs"
    }
];

// =====================================
// 🔹 SEARCH LOGIC
// =====================================
const searchInput =
    document.getElementById("search-input");

const searchResults =
    document.getElementById("search-results");

if (searchInput) {

    searchInput.addEventListener(
        "input",
        function (e) {

            const query =
                e.target.value.toLowerCase();

            if (query.length === 0) {

                searchResults.classList.add(
                    "hidden"
                );

                return;
            }

            const results =
                searchDatabase.filter(item =>

                    item.title
                        .toLowerCase()
                        .includes(query)

                    ||

                    item.desc
                        .toLowerCase()
                        .includes(query)

                    ||

                    item.category
                        .toLowerCase()
                        .includes(query)
                );

            if (results.length === 0) {

                searchResults.innerHTML = `
                    <div class="p-4 text-center text-gray-400">
                        No results found
                    </div>
                `;

                searchResults.classList.remove(
                    "hidden"
                );

                return;
            }

            searchResults.innerHTML =
                results.map(result => `

                <button
                    class="search-result-item
                    w-full
                    text-left
                    px-4
                    py-3
                    hover:bg-white/5
                    transition-colors
                    border-b
                    border-cyan-900/20
                    last:border-0"

                    data-page="${result.page}"
                >

                    <div class="flex items-start justify-between">

                        <div class="flex-1">

                            <p class="text-sm font-medium text-white">
                                ${result.title}
                            </p>

                            <p class="text-xs text-gray-400 mt-1">
                                ${result.desc}
                            </p>

                        </div>

                        <span class="
                            px-2 py-1 rounded-md
                            bg-cyan-500/20
                            text-cyan-400
                            text-xs ml-2
                            whitespace-nowrap
                        ">
                            ${result.category}
                        </span>

                    </div>

                </button>

            `).join("");

            searchResults.classList.remove(
                "hidden"
            );

            // Search item click
            document.querySelectorAll(
                ".search-result-item"
            ).forEach(item => {

                item.addEventListener(
                    "click",
                    function () {

                        navigateToPage(
                            this.dataset.page
                        );

                        searchInput.value = "";

                        searchResults.classList.add(
                            "hidden"
                        );
                    }
                );
            });
        }
    );
}

// Hide search dropdown
if (searchInput) {

    searchInput.addEventListener(
        "blur",
        () => {

            setTimeout(() => {

                searchResults.classList.add(
                    "hidden"
                );

            }, 200);
        }
    );
}


// =====================================
// 🔹 PROFILE MENU
// =====================================
const profileBtn =
    document.getElementById("profile-btn");

const profileMenu =
    document.getElementById("profile-menu");

if (profileBtn && profileMenu) {

    profileBtn.addEventListener(
        "click",
        function (e) {

            e.stopPropagation();

            profileMenu.classList.toggle(
                "hidden"
            );
        }
    );

    document.addEventListener(
        "click",
        function (e) {

            if (
                !profileBtn.contains(e.target)
                &&
                !profileMenu.contains(e.target)
            ) {

                profileMenu.classList.add(
                    "hidden"
                );
            }
        }
    );
}


// =====================================
// 🔹 NOTIFICATIONS
// =====================================
const notifications = [

    {
        icon: "⚠️",
        title: "Storm Alert",
        msg: "Wave activity increasing",
        time: "Now",
        color: "red"
    },

    {
        icon: "🌊",
        title: "Sea Level Rise",
        msg: "Mumbai port sea level elevated",
        time: "2 min ago",
        color: "orange"
    },

    {
        icon: "🐠",
        title: "Marine Update",
        msg: "Ocean conditions stable",
        time: "5 min ago",
        color: "emerald"
    }
];

let notificationIndex = 0;

const notificationBtn =
    document.getElementById("notification-btn");

if (notificationBtn) {

    notificationBtn.addEventListener(
        "click",
        function () {

            showNotificationToast(
                notifications[
                    notificationIndex %
                    notifications.length
                ]
            );

            notificationIndex++;
        }
    );
}


// =====================================
// 🔹 TOAST FUNCTION
// =====================================
function showNotificationToast(notif) {

    const colorMap = {

        red:
            "border-red-500 bg-red-500/10",

        orange:
            "border-orange-500 bg-orange-500/10",

        emerald:
            "border-emerald-500 bg-emerald-500/10"
    };

    const toast =
        document.createElement("div");

    toast.className = `
        fixed bottom-6 right-6
        p-4 rounded-xl border-l-4
        ${colorMap[notif.color]}
        shadow-lg z-50 max-w-sm
    `;

    toast.innerHTML = `

        <div class="flex items-start gap-3">

            <span class="text-2xl">
                ${notif.icon}
            </span>

            <div>

                <p class="font-semibold text-white">
                    ${notif.title}
                </p>

                <p class="text-sm text-gray-300 mt-1">
                    ${notif.msg}
                </p>

                <p class="text-xs text-gray-500 mt-1">
                    ${notif.time}
                </p>

            </div>

        </div>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 5000);
}

function openProfile() {

    alert(
        "MarineSense Admin\n\nVersion 1.0"
    );
}

function openPreferences() {

    alert(
        "Preferences panel coming soon."
    );
}

function logout() {

    localStorage.removeItem(
        "marine_login"
    );

    localStorage.removeItem(
        "marine_user"
    );

    window.location.href =
        "login.html";
}

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const username =
            document.getElementById(
                "username"
            );

        if (username) {

            username.innerText =
                localStorage.getItem(
                    "marine_user"
                ) || "Admin";
        }
    }
);
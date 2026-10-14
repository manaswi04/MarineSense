
/* =============================================
   MARINESENSE - DASHBOARD UI LOGIC
   ============================================= */

"use strict";

// =============================================
// NAVIGATION
// =============================================

function navigateToPage(pageName) {
    console.log("Opening page:", pageName);

    document.querySelectorAll(".nav-link").forEach(item => {
        item.classList.toggle("active", item.dataset.page === pageName);
    });

    document.querySelectorAll(".page-content").forEach(page => {
        page.classList.add("hidden");
    });

    const pageElement = document.getElementById(`${pageName}-page`);

    if (pageElement) {
        pageElement.classList.remove("hidden");
    } else {
        console.error(`Missing page: ${pageName}-page`);
    }

    const titles = {
        dashboard: "Ocean Analytics Dashboard",
        biodiversity: "Biodiversity Insights",
        risk: "Risk Analysis",
        advisory: "Advisory Reports",
        datasources: "Data Sources"
    };

    const pageTitle = document.getElementById("page-title");
    if (pageTitle) {
        pageTitle.textContent = titles[pageName] || "MarineSense";
    }

    if (pageName === "datasources") {
        if (typeof loadDataSources === "function") {
            loadDataSources();
        } else {
            console.warn("datasource.js is not loaded.");
        }
    }
}

// =============================================
// LOGGED-IN USER
// =============================================

function getLoggedInUser() {
    try {
        const storedUser = localStorage.getItem("marine_user");

        if (!storedUser) {
            console.warn("No marine_user found. Log in again if necessary.");
            return null;
        }

        const user = JSON.parse(storedUser);

        if (!user || typeof user !== "object" || Array.isArray(user)) {
            console.error("Invalid marine_user data.");
            return null;
        }

        // Support common nested API response structures.
        const actualUser = user.user || user.data?.user || user.data || user;

        return actualUser && typeof actualUser === "object"
            ? actualUser
            : null;

    } catch (error) {
        console.error("Unable to read MarineSense user:", error);
        return null;
    }
}

// =============================================
// PROFILE DISPLAY
// =============================================

function loadUserProfile() {
    const user = getLoggedInUser();

    const usernameElement = document.getElementById("username");
    const profileNameElement = document.getElementById("profile-name");
    const professionElement = document.getElementById("profile-profession");

    const avatarElement = document.getElementById("profile-avatar");
    const largeAvatarElement = document.getElementById("profile-avatar-large");

    if (!user) {
        if (usernameElement) usernameElement.textContent = "User";
        if (profileNameElement) profileNameElement.textContent = "User";
        if (professionElement) professionElement.textContent = "";
        if (avatarElement) avatarElement.textContent = "?";
        if (largeAvatarElement) largeAvatarElement.textContent = "?";
        return;
    }

    // IMPORTANT: Never assign the entire user object to a text element.
    const name =
        typeof user.name === "string" && user.name.trim()
            ? user.name.trim()
            : typeof user.username === "string" && user.username.trim()
                ? user.username.trim()
                : "User";

    const profession =
        typeof user.profession === "string"
            ? user.profession
            : "";

    const initials = name
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map(part => part.charAt(0).toUpperCase())
        .join("") || "?";

    if (usernameElement) usernameElement.textContent = name;
    if (profileNameElement) profileNameElement.textContent = name;
    if (professionElement) professionElement.textContent = profession;
    if (avatarElement) avatarElement.textContent = initials;
    if (largeAvatarElement) largeAvatarElement.textContent = initials;

    // Support older profile elements if they exist elsewhere in the HTML.
    const oldInitials = document.getElementById("profile-initials");
    const oldName = document.getElementById("profile-full-name");
    const oldLocation = document.getElementById("profile-location");

    if (oldInitials) oldInitials.textContent = initials;
    if (oldName) oldName.textContent = name;

    if (oldLocation) {
        oldLocation.textContent =
            user.portName || user.port || "";
    }
}

// Allow login code to refresh the profile after saving user data.
window.refreshMarineSenseProfile = loadUserProfile;

// =============================================
// PROFILE DROPDOWN
// =============================================

function initializeProfileMenu() {
    const profileBtn = document.getElementById("profile-btn");
    const profileMenu = document.getElementById("profile-menu");

    if (!profileBtn || !profileMenu) return;

    // Avoid registering duplicate event handlers.
    if (profileBtn.dataset.profileInitialized === "true") return;
    profileBtn.dataset.profileInitialized = "true";

    function closeMenu() {
        profileMenu.classList.add("hidden");
        profileBtn.setAttribute("aria-expanded", "false");
    }

    profileBtn.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();

        const isOpen = !profileMenu.classList.contains("hidden");
        profileMenu.classList.toggle("hidden", isOpen);
        profileBtn.setAttribute("aria-expanded", String(!isOpen));
    });

    profileMenu.addEventListener("click", function (event) {
        event.stopPropagation();
    });

    document.addEventListener("click", function (event) {
        if (
            !profileBtn.contains(event.target) &&
            !profileMenu.contains(event.target)
        ) {
            closeMenu();
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") closeMenu();
    });
}

// =============================================
// NAVIGATION CLICK EVENTS
// =============================================

function initializeNavigation() {
    document.querySelectorAll(".nav-link").forEach(item => {
        if (item.dataset.navigationInitialized === "true") return;
        item.dataset.navigationInitialized = "true";

        item.addEventListener("click", function (event) {
            event.preventDefault();
            navigateToPage(this.dataset.page);
        });
    });
}

// =============================================
// SEARCH
// =============================================

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

function initializeSearch() {
    const searchInput = document.getElementById("search-input");
    const searchResults = document.getElementById("search-results");

    if (!searchInput || !searchResults) return;

    searchInput.addEventListener("input", function () {
        const query = this.value.trim().toLowerCase();

        if (!query) {
            searchResults.classList.add("hidden");
            searchResults.innerHTML = "";
            return;
        }

        const results = searchDatabase.filter(item =>
            item.title.toLowerCase().includes(query) ||
            item.desc.toLowerCase().includes(query) ||
            item.category.toLowerCase().includes(query)
        );

        if (!results.length) {
            searchResults.innerHTML = `
                <div class="p-4 text-center text-gray-400">
                    No results found
                </div>
            `;
            searchResults.classList.remove("hidden");
            return;
        }

        searchResults.innerHTML = results.map(item => `
            <button
                type="button"
                class="search-result-item w-full text-left px-4 py-3
                       hover:bg-white/5 transition-colors border-b
                       border-cyan-900/20 last:border-0"
                data-page="${item.page}"
            >
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <p class="text-sm font-medium text-white">
                            ${item.title}
                        </p>
                        <p class="text-xs text-gray-400 mt-1">
                            ${item.desc}
                        </p>
                    </div>
                    <span class="px-2 py-1 rounded-md bg-cyan-500/20
                                 text-cyan-400 text-xs ml-2">
                        ${item.category}
                    </span>
                </div>
            </button>
        `).join("");

        searchResults.classList.remove("hidden");

        searchResults.querySelectorAll(".search-result-item").forEach(button => {
            button.addEventListener("click", function () {
                navigateToPage(this.dataset.page);
                searchInput.value = "";
                searchResults.classList.add("hidden");
            });
        });
    });

    searchInput.addEventListener("blur", function () {
        setTimeout(() => searchResults.classList.add("hidden"), 200);
    });
}

// =============================================
// NOTIFICATIONS
// =============================================

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

function showNotificationToast(notif) {
    const colorMap = {
        red: "border-red-500 bg-red-500/10",
        orange: "border-orange-500 bg-orange-500/10",
        emerald: "border-emerald-500 bg-emerald-500/10"
    };

    const toast = document.createElement("div");
    toast.className = `
        fixed bottom-6 right-6 p-4 rounded-xl border-l-4
        ${colorMap[notif.color] || ""}
        shadow-lg z-50 max-w-sm
    `;

    const icon = document.createElement("span");
    icon.className = "text-2xl";
    icon.textContent = notif.icon;

    const content = document.createElement("div");

    const title = document.createElement("p");
    title.className = "font-semibold text-white";
    title.textContent = notif.title;

    const message = document.createElement("p");
    message.className = "text-sm text-gray-300 mt-1";
    message.textContent = notif.msg;

    const time = document.createElement("p");
    time.className = "text-xs text-gray-500 mt-1";
    time.textContent = notif.time;

    content.append(title, message, time);
    toast.classList.add("flex", "items-start", "gap-3");
    toast.append(icon, content);
    document.body.appendChild(toast);

    setTimeout(() => toast.remove(), 5000);
}

function initializeNotifications() {
    const button = document.getElementById("notification-btn");
    if (!button || button.dataset.notificationInitialized === "true") return;

    button.dataset.notificationInitialized = "true";
    let index = 0;

    button.addEventListener("click", function () {
        showNotificationToast(notifications[index % notifications.length]);
        index++;
    });
}

// =============================================
// PROFILE SETTINGS AND PREFERENCES
// =============================================

function openProfile() {
    const menu = document.getElementById("profile-menu");
    const modal = document.getElementById("profile-settings-modal");

    if (menu) menu.classList.add("hidden");

    if (modal) {
        modal.classList.remove("hidden");

        const user = getLoggedInUser();

        const usernameInput = document.getElementById("settings-username");
        const locationInput = document.getElementById("settings-location");

        if (user && usernameInput) {
            usernameInput.value = user.username || "";
        }

        if (user && locationInput) {
            locationInput.value = user.portName || user.port || "";
        }
    } else {
        alert("MarineSense profile settings");
    }
}

function openProfileSettings() {
    openProfile();
}

function closeProfileSettings() {
    const modal = document.getElementById("profile-settings-modal");
    if (modal) modal.classList.add("hidden");
}

function openPreferences() {
    const menu = document.getElementById("profile-menu");
    const modal = document.getElementById("preferences-modal");

    if (menu) menu.classList.add("hidden");

    if (modal) {
        modal.classList.remove("hidden");
    } else {
        alert("Preferences panel coming soon.");
    }
}

function closePreferences() {
    const modal = document.getElementById("preferences-modal");
    if (modal) modal.classList.add("hidden");
}

// =============================================
// THEME
// =============================================

function changeTheme(theme) {
    const isLight = theme === "light";

    document.body.classList.toggle("bg-white", isLight);
    document.body.classList.toggle("bg-slate-950", !isLight);

    localStorage.setItem("marine_theme", isLight ? "light" : "dark");

    const radio = document.querySelector(
        `input[name="theme"][value="${isLight ? "light" : "dark"}"]`
    );

    if (radio) radio.checked = true;
}

function loadTheme() {
    const theme = localStorage.getItem("marine_theme") || "dark";
    changeTheme(theme);
}

// =============================================
// LOGOUT
// =============================================

function logout() {
    localStorage.removeItem("marine_login");
    localStorage.removeItem("marine_user");
    localStorage.removeItem("marine_token");

    window.location.href = "login.html";
}

// =============================================
// INITIALIZE DASHBOARD
// =============================================

function initializeMarineSense() {
    initializeNavigation();
    initializeSearch();
    initializeProfileMenu();
    initializeNotifications();
    loadUserProfile();
    loadTheme();

    // Set the default dashboard page.
    if (document.getElementById("dashboard-page")) {
        navigateToPage("dashboard");
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeMarineSense);
} else {
    initializeMarineSense();
}

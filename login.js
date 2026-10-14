// =====================================
// MARINESENSE - PROFILE MENU
// =====================================

(function () {
    "use strict";

    const profileBtn = document.getElementById("profile-btn");
    const profileMenu = document.getElementById("profile-menu");

    const usernameElement = document.getElementById("username");
    const profileNameElement = document.getElementById("profile-name");
    const professionElement = document.getElementById("profile-profession");

    const avatarElement = document.getElementById("profile-avatar");
    const largeAvatarElement = document.getElementById("profile-avatar-large");

    // -------------------------------------
    // LOAD LOGGED-IN USER
    // -------------------------------------

    function getLoggedInUser() {
        try {
            const storedUser = localStorage.getItem("marine_user");

            if (!storedUser) {
                return null;
            }

            const user = JSON.parse(storedUser);

            return user && typeof user === "object" && !Array.isArray(user)
                ? user
                : null;

        } catch (error) {
            console.error("Unable to read MarineSense user:", error);
            return null;
        }
    }

    // -------------------------------------
    // UPDATE PROFILE DETAILS
    // -------------------------------------

    function updateProfile() {
        const user = getLoggedInUser();

        if (!user) {
            if (usernameElement) usernameElement.textContent = "User";
            if (profileNameElement) profileNameElement.textContent = "User";
            if (professionElement) professionElement.textContent = "";
            if (avatarElement) avatarElement.textContent = "?";
            if (largeAvatarElement) largeAvatarElement.textContent = "?";

            console.warn("MarineSense user information not found.");
            return;
        }

        // Extract the name instead of displaying the entire JSON object.
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
            .map(part => part[0].toUpperCase())
            .join("") || "?";

        if (usernameElement) {
            usernameElement.textContent = name;
        }

        if (profileNameElement) {
            profileNameElement.textContent = name;
        }

        if (professionElement) {
            professionElement.textContent = profession;
        }

        if (avatarElement) {
            avatarElement.textContent = initials;
        }

        if (largeAvatarElement) {
            largeAvatarElement.textContent = initials;
        }
    }

    // -------------------------------------
    // PROFILE DROPDOWN
    // -------------------------------------

    if (profileBtn && profileMenu) {

        function closeMenu() {
            profileMenu.classList.add("hidden");
            profileBtn.setAttribute("aria-expanded", "false");
        }

        profileBtn.addEventListener("click", function (event) {
            event.stopPropagation();

            const isOpen = !profileMenu.classList.contains("hidden");

            profileMenu.classList.toggle("hidden", isOpen);

            profileBtn.setAttribute(
                "aria-expanded",
                String(!isOpen)
            );
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
            if (event.key === "Escape") {
                closeMenu();
            }
        });
    }

    // Initialize the profile.
    updateProfile();

    // Allow the profile to be refreshed after a login.
    window.refreshMarineSenseProfile = updateProfile;

})();
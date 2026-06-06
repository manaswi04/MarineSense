function login() {

    const email =
        document.getElementById(
            "email"
        ).value;

    const password =
        document.getElementById(
            "password"
        ).value;

    if (
        email ===
        "admin@marinesense.com"
        &&
        password ===
        "123456"
    ) {

        localStorage.setItem(
            "marine_login",
            "true"
        );

        localStorage.setItem(
            "marine_user",
            "Admin"
        );

        window.location.href =
            "index.html";
    }

    else {

        document.getElementById(
            "error"
        ).innerText =
            "Invalid Email or Password";
    }
}
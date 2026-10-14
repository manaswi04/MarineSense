async function signup() {

    const name =
        document.getElementById("name").value.trim();

    const username =
        document.getElementById("username").value.trim();

    const profession =
        document.getElementById("profession").value.trim();

    const location =
        document.getElementById("location").value.trim();

    const password =
        document.getElementById("password").value;

    const error =
        document.getElementById("error");

    if (
        !name ||
        !username ||
        !profession ||
        !location ||
        !password
    ) {
        error.innerText =
            "Please fill all fields.";

        return;
    }

    try {

        const response = await fetch(
            "http://127.0.0.1:8000/api/auth/signup",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    name,
                    username,
                    profession,
                    location,
                    password
                })
            }
        );

        const data =
            await response.json();

        if (data.status === "success") {

            alert(
                `Account created successfully!\n\nYour dashboard location: ${data.portName}`
            );

            window.location.href =
                "login.html";

        } else {

            error.innerText =
                data.message;

        }

    } catch (err) {

        error.innerText =
            "Unable to connect to server.";

        console.error(err);
    }
}
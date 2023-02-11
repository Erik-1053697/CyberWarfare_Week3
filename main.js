function setFormMessage(formElement, type, message) {
    const messageElement = formElement.querySelector(".form__message");

    messageElement.textContent = message;
    messageElement.classList.remove("form__message--success", "form__message--error");
    messageElement.classList.add(`form__message--${type}`);
}

function setInputError(inputElement, message) {
    inputElement.classList.add("form__input--error");
    inputElement.parentElement.querySelector(".form__input-error-message").textContent = message;
}

function clearInputError(inputElement) {
    inputElement.classList.remove("form__input--error");
    inputElement.parentElement.querySelector(".form__input-error-message").textContent = "";
}
var objPeople = [
    {
        username: "Test",
        password: "Test123"
    }
]

function getInfo() {
    var username = document.getElementById('username').value
    var password = document.getElementById('password').value

    for (var i = 0; i < objPeople.length; i++) {
        // check is user input matches username and password of a current index of the objPeople array
        if (username == objPeople[i].username && password == objPeople[i].password) {
            console.log(username + " is logged in!")
            window.location.href = "https://www.google.com"
            // stop the function if this is found to be true
            return;
        }
    }
    console.log("incorrect username or password")
    return "Incorrect username or password";
}

document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.querySelector("#login");
    const createAccountForm = document.querySelector("#createAccount");

    document.querySelector("#linkCreateAccount").addEventListener("click", e => {
        e.preventDefault();
        loginForm.classList.add("form--hidden");
        createAccountForm.classList.remove("form--hidden");
    });

    document.querySelector("#linkLogin").addEventListener("click", e => {
        e.preventDefault();
        loginForm.classList.remove("form--hidden");
        createAccountForm.classList.add("form--hidden");
    });

    // login klik
    loginForm.addEventListener("submit", e => {
        e.preventDefault();

        err = getInfo();
        if (err) { setFormMessage(loginForm, "error", `${err}`) }
    });

    document.querySelectorAll(".form__input").forEach(inputElement => {
        inputElement.addEventListener("blur", e => {
            if (e.target.id === "signupUsername" && e.target.value.length > 0 && e.target.value.length < 8) {
                setInputError(inputElement, "Username must be at least 8 characters in length");
            }
        });

        inputElement.addEventListener("input", e => {
            clearInputError(inputElement);
        });
    });
});
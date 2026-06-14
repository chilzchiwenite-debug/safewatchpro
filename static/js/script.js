document.addEventListener("DOMContentLoaded", function () {

    console.log("SafeWatch Pro Loaded");

    const flash = document.querySelector(".flash");

    if (flash) {
        setTimeout(function () {
            flash.style.display = "none";
        }, 3000);
    }

});
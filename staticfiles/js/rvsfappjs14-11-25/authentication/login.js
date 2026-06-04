// Refresh Captcha
document.getElementById('refresh_captcha').addEventListener('click', function() {
    fetch(refreshCaptchaUrl)  // we'll pass this dynamically from template
        .then(response => response.json())
        .then(data => {
            document.getElementById('captcha-container').innerHTML = data.captcha_html;
        })
        .catch(error => console.error('Error refreshing captcha:', error));
});

// Show Circular Loader with Fade-in on Form Submit
document.getElementById('loginForm').addEventListener('submit', function() {
    document.getElementById('submitBtn').disabled = true;  // disable submit button
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = 'flex';       // show overlay
    overlay.style.animation = 'fadeIn 0.5s ease forwards'; // trigger fade-in
});


// Auto-close Bootstrap alerts after 5 seconds
setTimeout(function() {
    let alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        let bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
    });
}, 5000);


// Toggle "Read More" content
function toggleReadMore() {
    var dots = document.getElementById("dots");
    var moreText = document.getElementById("more");
    var btnText = document.getElementById("readMoreBtn");

    if (dots.style.display === "none") {
        dots.style.display = "inline";
        moreText.style.display = "none";
        btnText.innerHTML = "Read more";
    } else {
        dots.style.display = "none";
        moreText.style.display = "inline";
        btnText.innerHTML = "Read less";
    }
}


// Function to restrict input to alphabets, numbers, spaces, dot, and comma
function restrictInput(event) {
    const regex = /^[a-zA-Z0-9 .,]*$/;
    if (!regex.test(event.target.value)) {
        // Replace anything not allowed
        event.target.value = event.target.value.replace(/[^a-zA-Z0-9 .,]/g, '');
    }
}

// Attach restriction to all input[type="text"] fields and textareas
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('input[type="text"], textarea').forEach(function(input) {
        input.addEventListener("input", restrictInput);
    });
});


document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("contact_form");
    const submitBtn = form.querySelector("button[type=submit]");

    form.addEventListener("submit", function () {
        submitBtn.disabled = true;
        submitBtn.innerText = "Submitting...";
    });
});


document.addEventListener("DOMContentLoaded", function () {
    const proceedBtn = document.getElementById("proceedSignup");
    if (proceedBtn) {
        proceedBtn.addEventListener("click", function () {
            const selected = document.getElementById("signupType").value;
            if (selected) {
                window.location.href = selected;  // redirect to selected signup page
            } else {
                alert("Please select an applicant type");
            }
        });
    }
});

// Run after page loads
document.addEventListener("DOMContentLoaded", function() {
    let radios = document.querySelectorAll("input[name='login_type']");
    let saved = localStorage.getItem("selectedLoginType");

    // Restore previously selected radio
    if (saved) {
        radios.forEach(r => {
            if (r.value === saved) {
                r.checked = true;
            }
        });
    }

    // Add click listener for redirect + save
    radios.forEach(radio => {
        radio.addEventListener("click", function() {
            localStorage.setItem("selectedLoginType", this.value);
            window.location.href = this.value;  // redirect
        });
    });
});
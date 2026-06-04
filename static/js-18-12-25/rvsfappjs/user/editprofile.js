// Password validation
document.addEventListener("DOMContentLoaded", () => {
    document.querySelector('form').addEventListener('submit', function (e) {
        const passwordInput = document.getElementById('password');
        const password = passwordInput.value;

        // Allow blank password (if user doesn't want to change it)
        if (password.trim() !== '') {
            const pattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$/;
            if (!pattern.test(password)) {
                e.preventDefault();
                alert("Password must be at least 8 characters long and include:\n- one uppercase letter\n- one lowercase letter\n- one number\n- one special character");
                passwordInput.focus();
            }
        }
    });

    // Username validation
    document.getElementById('username').addEventListener('input', function () {
        const usernameInput = this.value.trim();
        const errorElement = document.getElementById('username-error');
        const submitBtn = document.querySelector('button[type="submit"]');

        if (!/^\d+$/.test(usernameInput)) {
            errorElement.textContent = "Username must contain only numbers.";
            submitBtn.disabled = true;
            return;
        }

        if (usernameInput.length !== 10) {
            errorElement.textContent = "Username must be only 10 digits.";
            submitBtn.disabled = true;
            return;
        } else {
            errorElement.textContent = "";
            submitBtn.disabled = false;
            return;
        }
    });

    // Email validation
    document.getElementById('company_email').addEventListener('input', function () {
        const emailInput = this.value.trim();
        const errorElement = document.getElementById('email-error');
        const submitBtn = document.querySelector('button[type="submit"]');
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!emailPattern.test(emailInput)) {
            errorElement.textContent = "Enter a valid email address.";
            submitBtn.disabled = true;
        } else {
            errorElement.textContent = "";
            submitBtn.disabled = false;
        }
    });

    // Mobile number validation
    document.getElementById('auth_mobile').addEventListener('input', function () {
        const mobileInput = this.value.trim();
        const errorElement = document.getElementById('mobile-error');
        const submitBtn = document.querySelector('button[type="submit"]');

        if (!/^\d{10}$/.test(mobileInput)) {
            errorElement.textContent = "Enter a valid 10-digit mobile number.";
            submitBtn.disabled = true;
        } else {
            errorElement.textContent = "";
            submitBtn.disabled = false;
        }
    });
});

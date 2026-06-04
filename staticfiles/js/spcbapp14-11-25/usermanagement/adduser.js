document.getElementById("addUserForm").addEventListener("submit", function(e) {
        const password = document.querySelector('input[name="password"]').value;
        const confirmPassword = document.querySelector('input[name="confirmpassword"]').value;
        const mobile = document.querySelector('input[name="auth_mobile"]').value;
    
        // Password check
        if (password !== confirmPassword) {
            e.preventDefault();
            alert("Password and Confirm Password do not match!");
            return;
        }
    
        // Mobile number check
        const mobilePattern = /^[0-9]{10}$/;  // Only digits and exactly 10 digits
        if (!mobilePattern.test(mobile)) {
            e.preventDefault();
            alert("Please enter a valid 10-digit mobile number.");
            return;
        }
    });
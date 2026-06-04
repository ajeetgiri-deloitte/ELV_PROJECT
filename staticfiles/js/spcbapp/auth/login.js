  document.getElementById('refresh_captcha').addEventListener('click', function() {
        
        fetch(urlrefreshcatcha)
            .then(response => response.json())
            .then(data => {
                // alert(data.captcha_html);
                document.getElementById('captcha-container').innerHTML = data.captcha_html;
            })
            .catch(error => console.error('Error refreshing captcha:', error));
    });
 
const togglePassword = document.getElementById("togglePassword");
    const password = document.getElementById("password");

    togglePassword.addEventListener("click", () => {
      const type = password.getAttribute("type") === "password" ? "text" : "password";
      password.setAttribute("type", type);
      togglePassword.classList.toggle("fa-eye-slash");
    });

    // Basic validation
    const form = document.getElementById("loginForm");
    form.addEventListener("submit", function(e) {
      e.preventDefault();
      const email = document.getElementById("email").value.trim();
      const pass = password.value.trim();
      const emailError = document.getElementById("emailError");
      const passwordError = document.getElementById("passwordError");

      emailError.textContent = "";
      passwordError.textContent = "";

      if (!email) {
        emailError.textContent = "Email is required.";
        return;
      }
      if (!pass) {
        passwordError.textContent = "Password is required.";
        return;
      }

      // Submit logic here (e.g. AJAX or form submission)
      alert("Login submitted!");
    });

// Initialize Bootstrap tooltips after the DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Load State and District
$(document).ready(function () {
    const selectedState = $('#state').data('selected-state');
    const selectedDistrict = $('#district').data('selected-district');
    const url = $('#district-url').data('url');

    // If state was previously selected, trigger the change manually
    if (selectedState) {
        $('#state').val(selectedState);
        $.ajax({
            url: url,
            data: { 'state_id': selectedState },
            success: function (data) {
                $('#district').empty().append('<option disabled>Select District</option>');
                $.each(data, function (index, district) {
                    const selected = district.city_id == selectedDistrict ? 'selected' : '';
                    $('#district').append('<option value="' + district.city_id + '" ' + selected + '>' + district.city_name + '</option>');
                });
            }
        });
    }

    // Handle state change manually by user
    $('#state').change(function () {
        const stateId = $(this).val();
        if (stateId) {
            $.ajax({
                url: url,
                data: { 'state_id': stateId },
                success: function (data) {
                    $('#district').empty().append('<option selected disabled>Select District</option>');
                    $.each(data, function (index, district) {
                        $('#district').append('<option value="' + district.city_id + '">' + district.city_name + '</option>');
                    });
                }
            });
        }
    });
});

// Password and confirm password match
document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form');
    const passwordInput = document.getElementById('password');
    const confirmInput = document.getElementById('confirm_password');

    if (form && passwordInput && confirmInput) {
        form.addEventListener('submit', function (e) {
            const pass = passwordInput.value;
            const confirm = confirmInput.value;

            if (pass !== confirm) {
                e.preventDefault();
                alert("Passwords do not match.");
            }
        });
    }
});

// GST Error
document.addEventListener('DOMContentLoaded', function () {
    const gstInput = document.getElementById('gst_no');
    const gstError = document.getElementById('gst_error');

    if (gstInput && gstError) {
        // Instant validation and restrict input
        gstInput.addEventListener('input', () => {
            // Convert to uppercase
            let value = gstInput.value.toUpperCase();

            // Remove invalid characters (anything not 0-9 or A-Z)
            value = value.replace(/[^0-9A-Z]/g, '');

            // Limit to 15 characters
            if (value.length > 15) {
                value = value.slice(0, 15);
            }

            gstInput.value = value;

            // Show error if less than 15
            if (value.length > 0 && value.length < 15) {
                gstError.textContent = "GST number must be exactly 15 characters.";
                gstError.style.display = 'block';
            } else {
                gstError.style.display = 'none';
            }
        });
    }
});

//Fetch GST Deatils company name legal name etc.
$(document).ready(function() {
    const gstInput = $('#gst_no');
    const gstError = $('#gst_error');
    const companyInput = $('#company_name');
    const legalInput = $('#legal_name');
    const categoryInput = $('#business_category');
    const url = $('#gst-fetch-url').data('url'); // get URL from HTML

    if (gstInput.length && gstError.length && companyInput.length) {
        gstInput.blur(function() {
            const gstNo = $(this).val().trim();

            gstError.hide();

            if (gstNo.length !== 15) {
                gstError.text('GST number must be 15 characters').show();
                return;
            }

            companyInput.val('Loading...');
            legalInput.val('Loading...');
            categoryInput.val('Loading...');

            $.ajax({
                url: url,  // Use the URL from data attribute
                type: 'GET',
                data: { 'gst_no': gstNo },
                success: function(response) {
                    if (response.success) {
                        companyInput.val(response.company_name);
                        legalInput.val(response.legal_name);
                        categoryInput.val(response.business_category);
                    } else {
                        gstError.text(response.message || 'Invalid GST number').show();
                    }
                },
                error: function(xhr, status, error) {
                    gstError.text('Error fetching GST details. Please try again.').show();
                }
            });
        });
    }
});


$(document).ready(function() {
    const emailInput = $('#company_email');

    if (emailInput.length) {
        // Clear the default value on page load
        emailInput.val('');

        // Prevent browser autofill
        emailInput.attr('autocomplete', 'off');
    }
});


//For Company Pan Number
$(document).ready(function() {
    const panInput = $('#company_pan');
    const errorDiv = $('#pan_error');
    const form = $('form');

    if (panInput.length && errorDiv.length && form.length) {

        // Force uppercase while typing
        panInput.on('input', function() {
            this.value = this.value.toUpperCase();
        });

        // Validate PAN format on blur
        panInput.blur(function() {
            validatePAN();
        });

        // Validate before form submission
        form.submit(function(e) {
            if (!validatePAN()) {
                e.preventDefault(); // Stop form submission if PAN is invalid
                // Scroll to error for better UX
                $('html, body').animate({
                    scrollTop: panInput.offset().top - 100
                }, 500);
            }
        });

        function validatePAN() {
            const pan = panInput.val().trim();
            const panRegex = /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/;

            errorDiv.hide();

            if (pan === '') {
                errorDiv.text('PAN number is required').show();
                return false;
            }

            if (pan.length !== 10) {
                errorDiv.text('PAN must be exactly 10 characters').show();
                return false;
            }

            if (!panRegex.test(pan)) {
                errorDiv.text('Invalid PAN format. Use: AAAAA9999A (5 letters + 4 digits + 1 letter)').show();
                return false;
            }

            const firstFive = pan.substring(0, 5);
            const nextFour = pan.substring(5, 9);
            const lastChar = pan.charAt(9);

            if (!/^[A-Z]+$/.test(firstFive)) {
                errorDiv.text('First 5 characters must be letters').show();
                return false;
            }

            if (!/^\d{4}$/.test(nextFour)) {
                errorDiv.text('Characters 6-9 must be digits').show();
                return false;
            }

            if (!/^[A-Z]$/.test(lastChar)) {
                errorDiv.text('Last character must be a letter').show();
                return false;
            }

            return true; // PAN is valid
        }
    }
});

// For Company PINCODE
$(document).ready(function() {
    const pinInput = $('#pin_code');
    const errorDiv = $('#pin_code_error');
    const form = $('form');

    if (pinInput.length && errorDiv.length && form.length) {

        // Validate Pin Code on input (real-time)
        pinInput.on('input', function() {
            // Allow only numbers
            this.value = this.value.replace(/[^0-9]/g, '');
            validatePinCode();
        });

        // Validate on blur
        pinInput.blur(function() {
            validatePinCode();
        });

        // Validate before form submission
        form.submit(function(e) {
            if (!validatePinCode()) {
                e.preventDefault();
                // Scroll to error
                $('html, body').animate({
                    scrollTop: pinInput.offset().top - 100
                }, 500);
            }
        });

        function validatePinCode() {
            const pinCode = pinInput.val().trim();

            // Clear previous error
            errorDiv.hide().text('');

            if (pinCode === '') {
                errorDiv.text('Pin Code is required').show();
                return false;
            }

            if (pinCode.length !== 6) {
                errorDiv.text('Pin Code must be exactly 6 digits').show();
                return false;
            }

            if (!/^\d+$/.test(pinCode)) {
                errorDiv.text('Pin Code must contain only numbers').show();
                return false;
            }

            return true; // Valid
        }
    }
});

// For company Tin
$(document).ready(function() {
    const tinInput = $('#tin_no');
    const errorDiv = $('#tin_error');
    const form = $('form');

    if (tinInput.length && errorDiv.length && form.length) {

        // TIN No. validation - allow only numbers
        tinInput.on('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
            validateTIN();
        });

        // Validate on blur
        tinInput.blur(function() {
            validateTIN();
        });

        // Validate before form submission (if TIN is provided)
        form.submit(function(e) {
            const tinValue = tinInput.val().trim();
            if (tinValue !== '' && !validateTIN()) {
                e.preventDefault();
                $('html, body').animate({
                    scrollTop: tinInput.offset().top - 100
                }, 500);
            }
        });

        function validateTIN() {
            const tin = tinInput.val().trim();

            errorDiv.hide();

            if (tin === '') {
                return true; // optional field
            }

            if (tin.length !== 11) {
                errorDiv.text('TIN No. must be exactly 11 digits').show();
                return false;
            }

            if (!/^\d+$/.test(tin)) {
                errorDiv.text('TIN No. must contain only numbers').show();
                return false;
            }

            const firstTwoDigits = tin.substring(0, 2);
            if (firstTwoDigits === '00' || parseInt(firstTwoDigits) > 37) {
                errorDiv.text('Please enter a valid TIN No.').show();
                return false;
            }

            return true; // TIN is valid
        }
    }
});


//For CIN And IEC
$(document).ready(function() {
    const cinInput = $('#cin');
    const iecInput = $('#iec');
    const form = $('form');

    if (cinInput.length && iecInput.length && form.length) {

        // CIN Validation - uppercase
        cinInput.on('input', function() {
            this.value = this.value.toUpperCase();
            validateCIN();
        });

        cinInput.blur(function() {
            validateCIN();
        });

        // IEC Validation - numbers only
        iecInput.on('input', function() {
            this.value = this.value.replace(/[^0-9]/g, '');
            validateIEC();
        });

        iecInput.blur(function() {
            validateIEC();
        });

        // Validate before form submission (if fields provided)
        form.submit(function(e) {
            const cinValue = cinInput.val().trim();
            const iecValue = iecInput.val().trim();

            let isValid = true;

            if (cinValue !== '' && !validateCIN()) isValid = false;
            if (iecValue !== '' && !validateIEC()) isValid = false;

            if (!isValid) {
                e.preventDefault();
                const firstError = $('.text-danger:visible').first();
                if (firstError.length) {
                    $('html, body').animate({
                        scrollTop: firstError.offset().top - 100
                    }, 500);
                }
            }
        });

        function validateCIN() {
            const cin = cinInput.val().trim();
            const errorDiv = $('#cin_error');
            const cinRegex = /^[A-Z]{1}[0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$/;

            errorDiv.hide();

            if (cin === '') return true;
            if (cin.length !== 21) {
                errorDiv.text('CIN must be exactly 21 characters').show();
                return false;
            }
            if (!cinRegex.test(cin)) {
                errorDiv.text('Invalid CIN format. Format: A99999AA9999AAA999999').show();
                return false;
            }
            return true;
        }

        function validateIEC() {
            const iec = iecInput.val().trim();
            const errorDiv = $('#iec_error');

            errorDiv.hide();
            if (iec === '') return true;
            if (iec.length !== 10) {
                errorDiv.text('IEC must be exactly 10 digits').show();
                return false;
            }
            if (!/^\d+$/.test(iec)) {
                errorDiv.text('IEC must contain only numbers').show();
                return false;
            }
            if (iec.charAt(0) === '0') {
                errorDiv.text('IEC cannot start with 0').show();
                return false;
            }
            return true;
        }
    }
});



//For otp verfication
$(document).ready(function() {
    const cooldownTimers = {};
    // --- COOLDOWN FUNCTION ---
    function startCooldown($button, seconds, otpType) {
        let remaining = seconds;
        $button.prop('disabled', true).text(`Resend in ${remaining}s`);

        if (cooldownTimers[otpType]) clearInterval(cooldownTimers[otpType]);

        cooldownTimers[otpType] = setInterval(() => {
            remaining--;
            if (remaining > 0) {
                $button.text(`Resend in ${remaining}s`);
            } else {
                clearInterval(cooldownTimers[otpType]);
                $button.prop('disabled', false).text('Resend OTP');
            }
        }, 1000);
    }

    // --- GENERATE OTP ---
    function generateOTP(otpType, button) {
        const $button = $(button);
        let value, containerId;

        if (otpType === 'company_email') {
            value = $('#company_email').val().trim();
            containerId = '#company_email_otp_container';
        } else if (otpType === 'auth_email') {
            value = $('#auth_email').val().trim();
            containerId = '#auth_email_otp_container';
        } else if (otpType === 'auth_mobile') {
            value = $('#auth_mobile').val().trim();
            containerId = '#auth_mobile_otp_container';
        }

        if (!value) { alert(`Please enter ${otpType.replace(/_/g, ' ')} first`); return; }

        if (otpType.includes('email') && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
            alert('Please enter a valid email address'); return;
        }
        if (otpType === 'auth_mobile' && !/^[6-9]\d{9}$/.test(value)) {
            alert('Please enter a valid 10-digit mobile number'); return;
        }

        $button.prop('disabled', true).text('Sending...');
        startCooldown($button, 30, otpType);

        $.ajax({
            url: generateOtpUrl,
            type: 'POST',
            contentType: 'application/json',
            headers: { 'X-CSRFToken': csrfToken },
            data: JSON.stringify({ otp_type: otpType, authorization: value }),
            success: function(response) {
                if (response.success) {
                    alert('OTP sent successfully');
                    showOTPInputField(otpType, containerId);
                    $button.hide();
                } else {
                    alert('Error: ' + response.message);
                    clearInterval(cooldownTimers[otpType]);
                    $button.prop('disabled', false).text('Get OTP');
                }
            },
            error: function() {
                alert('Error generating OTP. Please try again.');
                clearInterval(cooldownTimers[otpType]);
                $button.prop('disabled', false).text('Get OTP');
            }
        });
    }

    // --- SHOW OTP INPUT FIELD ---
    function showOTPInputField(otpType, containerId) {
        const $container = $(containerId);
        $container.empty().append(`
            <div class="otp-input-group">
                <input type="text" class="form-control otp-input" data-type="${otpType}" placeholder="Enter OTP" maxlength="6">
                <button type="button" class="btn btn-primary verify-otp-btn">Verify</button>
                <button type="button" class="btn btn-link resend-otp-btn" style="display:none;">Resend OTP</button>
            </div>
        `);
    }

    // --- VERIFY OTP ---
    $(document).on('click', '.verify-otp-btn', function() {
        const $otpInput = $(this).siblings('.otp-input');
        const otpType = $otpInput.data('type');
        const otp = $otpInput.val();
        if (!otp) { alert("Please enter the OTP."); return; }
        if (otp.length !== 6) { alert("OTP must be 6 digits"); return; }

        const $btn = $(this);
        let value = otpType === 'company_email' ? $('#company_email').val().trim() :
                    otpType === 'auth_email' ? $('#auth_email').val().trim() :
                    $('#auth_mobile').val().trim();

        $btn.prop('disabled', true).text('Verifying...');

        $.ajax({
            url: verifyOtpUrl,
            type: 'POST',
            contentType: 'application/json',
            headers: { 'X-CSRFToken': csrfToken },
            data: JSON.stringify({ otp_type: otpType, otp: otp, authorization: value }),
            success: function(response) {
                if (response.success) {
                    $otpInput.prop('readonly', true);
                    $btn.text('Verified').removeClass('btn-primary').addClass('btn-success').prop('disabled', true);
                    $('#is_' + otpType + '_verified').val('true');
                    $('#get_' + otpType + '_otp_btn').text('Verified').removeClass('btn-primary').addClass('btn-success').prop('disabled', true);
                    alert('OTP verified successfully');
                } else {
                    alert('Error: ' + response.message);
                    $btn.prop('disabled', false).text('Verify');
                }
            },
            error: function() {
                alert('Error verifying OTP');
                $btn.prop('disabled', false).text('Verify');
            }
        });
    });

    // --- RESEND OTP ---
    $(document).on('click', '.resend-otp-btn', function() {
        const $otpInput = $(this).siblings('.otp-input');
        const otpType = $otpInput.data('type');
        generateOTP(otpType, $('#get_' + otpType + '_otp_btn')[0]);
        $(this).hide();
    });

    // --- ATTACH BUTTON EVENTS ---
    $(document).on('click', '.otp-btn', function() {
        const otpType = $(this).data('otp-type');
        generateOTP(otpType, this);
    });

    // --- RESET OTP ON FIELD CHANGE ---
    $('#company_email, #auth_email, #auth_mobile').on('input', function() {
        const fieldId = $(this).attr('id');
        const otpType = fieldId;
        $('#is_' + otpType + '_verified').val('false');
        $('#get_' + otpType + '_otp_btn').show().prop('disabled', false).text('Get OTP').removeClass('btn-success').addClass('btn-primary');
        $('#' + otpType + '_otp_container').empty();
        if (cooldownTimers[otpType]) { clearInterval(cooldownTimers[otpType]); cooldownTimers[otpType] = null; }
    });

});


//For Password and confirm password
document.addEventListener('DOMContentLoaded', function () {
    const passwordField = document.getElementById('password');
    const confirmPasswordField = document.getElementById('confirm_password');

    const togglePassword = document.getElementById('togglePassword');
    const toggleConfirmPassword = document.getElementById('toggleConfirmPassword');

    const passwordError = document.getElementById('passwordError');
    const confirmPasswordError = document.getElementById('confirmPasswordError');

    // Toggle password visibility
    togglePassword.addEventListener('click', function () {
        const isPassword = passwordField.type === 'password';
        passwordField.type = isPassword ? 'text' : 'password';
        this.textContent = isPassword ? '🙈' : '👁️';
    });

    toggleConfirmPassword.addEventListener('click', function () {
        const isPassword = confirmPasswordField.type === 'password';
        confirmPasswordField.type = isPassword ? 'text' : 'password';
        this.textContent = isPassword ? '🙈' : '👁️';
    });

    // Validate on blur
    passwordField.addEventListener('blur', validatePassword);
    confirmPasswordField.addEventListener('blur', validateConfirmPassword);

    function validatePassword() {
        const password = passwordField.value;
        const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?#&])[A-Za-z\d@$!%*?#&]{8,}$/;

        if (!regex.test(password)) {
            passwordError.style.display = 'block';
            passwordError.textContent = "Password must be at least 8 characters and include uppercase, lowercase, number, and special character.";
            passwordField.classList.add('is-invalid');
            return false;
        } else {
            passwordError.style.display = 'none';
            passwordField.classList.remove('is-invalid');
            passwordField.classList.add('is-valid');
            return true;
        }
    }

    function validateConfirmPassword() {
        const password = passwordField.value;
        const confirmPassword = confirmPasswordField.value;

        if (password !== confirmPassword) {
            confirmPasswordError.style.display = 'block';
            confirmPasswordError.textContent = "Password and confirm Password do not match.";
            confirmPasswordField.classList.add('is-invalid');
            return false;
        } else {
            confirmPasswordError.style.display = 'none';
            confirmPasswordField.classList.remove('is-invalid');
            confirmPasswordField.classList.add('is-valid');
            return true;
        }
    }
});



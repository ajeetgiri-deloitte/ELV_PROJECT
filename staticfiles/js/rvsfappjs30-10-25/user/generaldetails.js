
// ================= Fill Geolocation =================
function fillLocation() {
    if (!navigator.geolocation) {
        alert('Geolocation not supported by your browser');
        return;
    }
    navigator.geolocation.getCurrentPosition(
        position => {
            document.getElementById('id_latitude').value  = position.coords.latitude.toFixed(6);
            document.getElementById('id_longitude').value = position.coords.longitude.toFixed(6);
        },
        err => {
            alert('Unable to retrieve your location: ' + err.message);
        }
    );
}

const pincodeField = document.getElementById("id_pin_code");
pincodeField.addEventListener("input", function () {
        // Remove anything that is not a digit
        this.value = this.value.replace(/\D/g, '');
    });
// ================= Toggle PDF Upload for Documents =================
document.addEventListener("DOMContentLoaded", function() {
    const fields = [
        { no: "id_gst_no", pdf: "gst_pdf_wrapper" },
        { no: "id_pan_no", pdf: "pan_pdf_wrapper" },
        { no: "id_tin_no", pdf: "tin_pdf_wrapper" },
        { no: "id_cin_no", pdf: "cin_pdf_wrapper" },
        { no: "id_iec_no", pdf: "iec_pdf_wrapper" }
    ];

    fields.forEach(field => {
        const noInput = document.getElementById(field.no);
        const pdfWrapper = document.getElementById(field.pdf);
        const fileInput = pdfWrapper.querySelector("input");

        function togglePDF() {
            if (noInput.value.trim() !== "") {
                pdfWrapper.style.display = "block";
                fileInput.setAttribute("required", "required");
            } else {
                pdfWrapper.style.display = "none";
                fileInput.removeAttribute("required");
                fileInput.value = ""; // clear file if hidden
            }
        }

        // Initial check on load
        togglePDF();

        // Watch for changes
        noInput.addEventListener("input", togglePDF);
    });
});

// ================= MN File PDF Validation =================
document.addEventListener("DOMContentLoaded", function() {
    const fileInputs = document.querySelectorAll("input[type='file']");
    fileInputs.forEach(input => {
        input.addEventListener("change", function() {
            const file = this.files[0];
            if (!file) return;

            const maxSizeMB = 2;
            const maxSizeBytes = maxSizeMB * 1024 * 1024;

            if (file.type !== 'application/pdf') {
                alert('Invalid file type. Please upload a PDF.');
                this.value = '';
            } else if (file.size > maxSizeBytes) {
                alert('File is too large. Maximum allowed size is 2 MB.');
                this.value = '';
            }
        });
    });
});

// ================= Form Validation Before Next =================
document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");
    const errorBox = document.createElement("div");
    errorBox.className = "alert alert-danger mt-3";
    errorBox.style.display = "none";
    errorBox.innerText = "⚠️ Please fill out all required fields before continuing.";
    form.prepend(errorBox);

    form.addEventListener("submit", function (event) {
        const requiredFields = form.querySelectorAll("[required]");
        let allFilled = true;

        requiredFields.forEach(field => {
            if (!field.value || field.value.trim() === "") {
                allFilled = false;
                field.classList.add("is-invalid");
            } else {
                field.classList.remove("is-invalid");
            }
        });

        if (!allFilled) {
            event.preventDefault(); // Stop form submission
            errorBox.style.display = "block"; // Show common error message
            window.scrollTo({ top: 0, behavior: "smooth" }); // Scroll to top
        } else {
            errorBox.style.display = "none"; // Hide error if valid
        }
    });
});


$(document).ready(function () {
    var selectedState = $("#state").data("selected");     // <-- Comes from template
    var selectedDistrict = $("#district").data("selected");
    const url = $('#district-url').data('url');
    console.log(selectedState);
    console.log(selectedDistrict);
    
    

    if (selectedState) {
        $('#state').val(selectedState); // Preselect state
        $.ajax({
            url: url,
            data: { 'state_id': selectedState },
            success: function (data) {
                $('#district').empty().append('<option disabled>Select District</option>');
                $.each(data, function (index, district) {
                    var selected = (district.city_id.toString() === selectedDistrict.toString()) ? 'selected' : '';
                    $('#district').append('<option value="' + district.city_id + '" ' + selected + '>' + district.city_name + '</option>');
                });
            }
        });
    }

    $('#state').change(function () {
        var stateId = $(this).val();
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

document.addEventListener('DOMContentLoaded', function () {
    const stateSelect = document.getElementById('state');
    const consentInput = document.getElementById('id_cto_number');
    const gpcbidInput = document.getElementById('gpcbid-field');
    const gpcbidContainer = document.getElementById('gpcbid-container');
    const consentTick = document.getElementById('consent-tick');
    const consentCross = document.getElementById('consent-cross');
    const gpcbidTick = document.getElementById('gpcbid-tick');
    const gpcbidCross = document.getElementById('gpcbid-cross');

    const stateMap = {
        'Karnataka': { code: 'KTK', status: 0 },
        'Madhya Pradesh': { code: 'MP', status: 0 },
        'Maharashtra': { code: 'MAH', status: 0 },
        'Gujarat': { code: 'GUJ', status: 0 },
        'Rajasthan': { code: 'RJ', status: 0 }
    };

    function toggleGpcbid() {
        const selectedOption = stateSelect.options[stateSelect.selectedIndex];
        const text = selectedOption?.textContent?.trim() || selectedOption?.text || '';
        const show = (text === 'Gujarat');
        gpcbidContainer.style.display = show ? 'block' : 'none';
        if (gpcbidInput) gpcbidInput.required = show;
    }

    async function validateConsent() {
        // Reset all indicators
        consentTick.style.display = 'none';
        consentCross.style.display = 'none';
        gpcbidTick.style.display = 'none';
        gpcbidCross.style.display = 'none';

        const selectedOption = stateSelect.options[stateSelect.selectedIndex];
        const selectedText = selectedOption?.textContent?.trim() || selectedOption?.text || '';
        const consentId = consentInput.value.trim();
        
        // Don't validate if no consent ID
        if (!consentId) return;

        const mapping = stateMap[selectedText] || { code: 'UP', status: 1 };
        
        // For Gujarat, don't validate if no GPCB ID
        if (mapping.code === 'GUJ' && (!gpcbidInput || !gpcbidInput.value.trim())) {
            return;
        }

        const payload = {
            consent_id: consentId,
            statecode: mapping.code,
            status: mapping.status
        };

        if (mapping.code === 'GUJ' && gpcbidInput) {
            payload.gpcbid = gpcbidInput.value.trim();
        }

        try {
            const response = await fetch('/rvsf/consent/details/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            console.log('Validation response:', data); // Debug log
            
            if (response.status === 200 && data.status === 200 && data.data && data.data.applicationNo) {
                // Success case
                consentTick.style.display = 'inline';
                consentTick.style.color = 'green';
                if (mapping.code === 'GUJ') {
                    gpcbidTick.style.display = 'inline';
                    gpcbidTick.style.color = 'green';
                }
            } else {
                // Error case
                consentCross.style.display = 'inline';
                consentCross.style.color = 'red';
                if (mapping.code === 'GUJ') {
                    gpcbidCross.style.display = 'inline';
                    gpcbidCross.style.color = 'red';
                }
                // Optional: Show error message if you add an error element
                // const errorBox = document.getElementById('consent-error');
                // if (errorBox) errorBox.textContent = data.error || data.message || 'Validation failed';
            }
        } catch (error) {
            console.error('Network error:', error);
            consentCross.style.display = 'inline';
            consentCross.style.color = 'red';
        }
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Initialize
    toggleGpcbid();
    
    // Event listeners
    stateSelect.addEventListener('change', toggleGpcbid);
    stateSelect.addEventListener('change', validateConsent);
    consentInput.addEventListener('input', validateConsent);
    if (gpcbidInput) {
        gpcbidInput.addEventListener('input', validateConsent);
    }
});

// $(document).ready(function () {
//         var selectedState = "{{ form_data.state|default:'' }}";
//         var selectedDistrict = "{{ form_data.district|default:'' }}";
//         const url = $('#district-url').data('url');

//         // If state was previously selected, trigger the change manually
//         if (selectedState) {
//             $('#state').val(selectedState); // Preselect state
//             $.ajax({
//                 url: url,
//                 data: { 'state_id': selectedState },
//                 success: function (data) {
//                     $('#district').empty().append('<option disabled>Select District</option>');
//                     $.each(data, function (index, district) {
//                         var selected = (district.city_id.toString() === selectedDistrict.toString()) ? 'selected' : '';
//                         $('#district').append('<option value="' + district.city_id + '" ' + selected + '>' + district.city_name + '</option>');
//                     });
//                 }
//             });
//         }

//         // Handle state change manually by user
//         $('#state').change(function () {
//             var stateId = $(this).val();
//             if (stateId) {
//                 $.ajax({
//                     url: url,
//                     data: { 'state_id': stateId },
//                     success: function (data) {
//                         $('#district').empty().append('<option selected disabled>Select District</option>');
//                         $.each(data, function (index, district) {
//                             $('#district').append('<option value="' + district.city_id + '">' + district.city_name + '</option>');
//                         });
//                     }
//                 });
//             }
//         });
//     });
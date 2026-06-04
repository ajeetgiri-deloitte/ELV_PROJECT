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
    const iecInput = document.getElementById('id_iec_no');
    const iecUploadContainer = document.querySelector('.col-md-6.mb-4:has(input[name="iec_pdf"])');
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

     function toggleIECUpload() {
        if (iecInput.value.trim() !== '') {
            // Show IEC upload field
            iecUploadContainer.style.display = 'block';
            // Make the file input required
            const fileInput = iecUploadContainer.querySelector('input[name="iec_pdf"]');
            if (fileInput) {
                fileInput.required = true;
            }
        } else {
            // Hide IEC upload field
            iecUploadContainer.style.display = 'none';
            // Remove required attribute
            const fileInput = iecUploadContainer.querySelector('input[name="iec_pdf"]');
            if (fileInput) {
                fileInput.required = false;
            }
        }
    }
    
    // Initial toggle based on existing value
    toggleIECUpload();
    
    // Add event listener for input changes
    iecInput.addEventListener('input', toggleIECUpload);
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
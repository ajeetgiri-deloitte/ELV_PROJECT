// For tool tip
$(document).ready(function () {
    // Enable all Bootstrap tooltips on the page
    $('[data-bs-toggle="tooltip"]').tooltip();
});

// Gst Fetch Details and validation error message shown.
$(document).ready(function () {
    const gstInput = $("#id_gst_no");
    const companyInput = $("#company_name");
    const legalInput = $("#legal_name");
    const businessInput = $("#business_category");
    const errorDiv = $("#gst_error");

    // GSTIN Format (15 chars: state code + PAN + entity + Z + checksum)
    const gstRegex = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;

    gstInput.on("blur", function () {
        const gstNo = gstInput.val().trim().toUpperCase();

        if (!gstNo) {
            errorDiv.text("");
            gstInput.removeClass("is-invalid is-valid");
            return;
        }

        // Validate GST format
        if (!gstRegex.test(gstNo)) {
            errorDiv.html(
                "Invalid GST format. Please enter a valid 15-digit GST Number.<br>" +
                "Example: <strong>22ABCDE1234F1Z5</strong>"
            );
            gstInput.addClass("is-invalid").removeClass("is-valid");
            companyInput.val("");
            legalInput.val("");
            businessInput.val("");
            return;
        }

        // If valid → fetch details
        gstInput.removeClass("is-invalid").addClass("is-valid");
        errorDiv.text("");

        // Show loading placeholders
        companyInput.val("Loading...");
        legalInput.val("Loading...");
        businessInput.val("Loading...");

        $.ajax({
            url: window.appConfig.fetchGstUrl,
            type: "GET",
            data: { gst_no: gstNo },
            dataType: "json",
            success: function (data) {
                if (data.success) {
                    companyInput.val(data.company_name || "");
                    legalInput.val(data.legal_name || "");
                    businessInput.val(data.business_category || "");
                } else {
                    errorDiv.text(data.error || "Failed to fetch GST details.");
                    companyInput.val("");
                    legalInput.val("");
                    businessInput.val("");
                    gstInput.addClass("is-invalid").removeClass("is-valid");
                }
            },
            error: function (xhr, status, error) {
                errorDiv.text("Something went wrong. Please try again.");
                console.error("GST Fetch Error:", error);
                companyInput.val("");
                legalInput.val("");
                businessInput.val("");
                gstInput.addClass("is-invalid").removeClass("is-valid");
            }
        });
    });
});


// For select District
$(document).ready(function () {
    $("#state").change(function () {
        let stateName = $(this).val();

        let districtSelect = $("#district"); // ✅ matches your template
        districtSelect.empty();
        districtSelect.append('<option value="" selected disabled>Select District</option>');

        if (stateName) {
            $.ajax({
                url: window.appConfig.ajaxLoadDistrictsUrl,  // /ajax/load-districts/
                method: "GET",
                data: { state_name: stateName },   // ✅ matches your view
                success: function (response) {
                    if (Array.isArray(response) && response.length > 0) {
                        $.each(response, function (index, district) {
                            districtSelect.append(
                                $("<option>", {
                                    value: district.city_name, // or district.city_id if you want ID
                                    text: district.city_name
                                })
                            );
                        });
                    } else {
                        districtSelect.append('<option value="" disabled>No districts found</option>');
                    }
                },
                error: function () {
                    alert("Error loading districts");
                }
            });
        }
    });
});

// Company Email, Pan And user Email, Pan should not same validation
$(document).ready(function () {
    let companyEmailField = $("#company_email");
    let personEmailField = $("#authorized_person_email");

    let companyPanField = $("#company_pan, #id_company_pan");
    let personPanField = $("#authorized_person_pan, #id_auth_pan");

    let submitBtn = $("form[action='/consumer/bulk-consumer-signup/'] button[type='submit']");

    // Add error placeholders if not already present
    if ($("#email-error").length === 0) {
        personEmailField.after('<div id="email-error" class="text-danger mt-1" style="display:none;"></div>');
    }
    if ($("#pan-error").length === 0) {
        personPanField.after('<div id="pan-error" class="text-danger mt-1" style="display:none;"></div>');
    }

    function validateEmails() {
        let companyEmail = companyEmailField.val().trim();
        let personEmail = personEmailField.val().trim();

        if (companyEmail && personEmail && companyEmail.toLowerCase() === personEmail.toLowerCase()) {
            $("#email-error").text("Company Email and Authorized Person Email cannot be the same.").show();
            disableSubmit();
            return false;
        } else {
            $("#email-error").hide().text("");
            enableSubmit();
            return true;
        }
    }

    function validatePAN() {
        let companyPan = companyPanField.val().trim();
        let personPan = personPanField.val().trim();

        if (companyPan && personPan && companyPan.toUpperCase() === personPan.toUpperCase()) {
            $("#pan-error").text("Company PAN and Authorized Person PAN cannot be the same.").show();
            disableSubmit();
            return false;
        } else {
            $("#pan-error").hide().text("");
            enableSubmit();
            return true;
        }
    }

    function disableSubmit() {
        submitBtn.prop("disabled", true);
    }

    function enableSubmit() {
        // Only enable if there are no visible errors
        if ($("#email-error:visible").length === 0 && $("#pan-error:visible").length === 0) {
            submitBtn.prop("disabled", false);
        }
    }

    // Validate while typing (live)
    companyEmailField.on("input blur", validateEmails);
    personEmailField.on("input blur", validateEmails);

    companyPanField.on("input blur", validatePAN);
    personPanField.on("input blur", validatePAN);

    // Initial check (in case of prefilled values)
    validateEmails();
    validatePAN();
});


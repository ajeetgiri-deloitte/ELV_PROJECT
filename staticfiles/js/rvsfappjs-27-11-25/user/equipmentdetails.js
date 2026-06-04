// ================= PDF Validation =================
document.addEventListener("DOMContentLoaded", function () {
    const pdfInput = document.getElementById("geo_pdf");
    if (pdfInput) {
        pdfInput.addEventListener("change", function () {
            const file = this.files[0];
            if (file) {
                const maxSizeBytes = 2 * 1024 * 1024; // 2 MB
                const isPDF = file.type === "application/pdf";
                const isSizeOK = file.size <= maxSizeBytes;

                if (!isPDF) {
                    alert("Invalid file type. Please upload a PDF.");
                    this.value = "";
                } else if (!isSizeOK) {
                    alert("File is too large. Maximum allowed size is 2 MB.");
                    this.value = "";
                }
            }
        });
    }
});

// ================= Toggle "Other Equipment" Input =================
function toggleOtherInput(select) {
    const otherInputDiv = document.getElementById("other_equipment_div");
    if (otherInputDiv) {
        otherInputDiv.style.display = (select.value === "7") ? "block" : "none";
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const equipmentSelect = document.getElementById("equipment_name");
    if (equipmentSelect) {
        toggleOtherInput(equipmentSelect);
        equipmentSelect.addEventListener("change", function () {
            toggleOtherInput(this);
        });
    }
});

// ================= Video Validation & Preview =================
document.addEventListener("DOMContentLoaded", function () {
    const videoInput = document.getElementById("geo_video");
    const errorMsg = document.getElementById("videoError");
    const videoPreview = document.getElementById("videoPreview");
    const form = document.getElementById("rvsfForm");

    if (videoInput) {
        videoInput.addEventListener("change", function () {
            const file = this.files[0];
            if (!errorMsg || !videoPreview) return;

            // Reset
            errorMsg.classList.add("d-none");
            this.classList.remove("is-invalid");
            videoPreview.classList.add("d-none");
            videoPreview.removeAttribute("src");

            if (file) {
                const maxSizeBytes = 20 * 1024 * 1024; // 20 MB

                if (file.type !== "video/mp4") {
                    errorMsg.textContent = "Only MP4 video format is allowed.";
                    errorMsg.classList.remove("d-none");
                    this.classList.add("is-invalid");
                    return;
                }

                if (file.size > maxSizeBytes) {
                    errorMsg.textContent = "Video size must be 20 MB or less.";
                    errorMsg.classList.remove("d-none");
                    this.classList.add("is-invalid");
                    return;
                }

                // Preview
                const videoURL = URL.createObjectURL(file);
                videoPreview.src = videoURL;
                videoPreview.classList.remove("d-none");
            }
        });
    }

    // Block form submit if video invalid
    if (form) {
        form.addEventListener("submit", function (event) {
            const file = videoInput ? videoInput.files[0] : null;
            if (file) {
                const maxSizeBytes = 20 * 1024 * 1024;
                if (file.type !== "video/mp4" || file.size > maxSizeBytes) {
                    if (errorMsg) errorMsg.classList.remove("d-none");
                    if (videoInput) videoInput.classList.add("is-invalid");
                    event.preventDefault();
                }
            }
        });
    }
});

// ================= Form Validation on Next Button =================
document.addEventListener("DOMContentLoaded", function () {
    const nextBtn = document.getElementById("nextBtn");
    const form = document.getElementById("rvsfForm");
    const errorMsg = document.getElementById("formError");

    if (nextBtn && form) {
        nextBtn.addEventListener("click", function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                if (errorMsg) errorMsg.classList.remove("d-none");
                form.reportValidity();

                setTimeout(function () {
                    if (errorMsg) errorMsg.classList.add("d-none");
                }, 10000);
            }
        });
    }
});

// ================= Table Row Check Before Next =================
$(document).ready(function () {
    $("#nextBtn").on("click", function (e) {
        let rowCount = $("table tbody tr").length;

        if (rowCount === 0) {
            alert("Please add at least one equipment detail before proceeding.");
            e.preventDefault();
            return false;
        }

        // If rows exist, submit form (replace with your logic if needed)
        $("#yourFormId").submit();
    });
});

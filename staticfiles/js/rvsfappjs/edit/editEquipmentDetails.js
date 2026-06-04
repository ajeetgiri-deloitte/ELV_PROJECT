// PDF validation
document.getElementById('geo_pdf').addEventListener('change', function () {
    const fileInput = this;
    const file = fileInput.files[0];

    if (file) {
        const maxSizeMB = 2;
        const maxSizeBytes = maxSizeMB * 1024 * 1024;

        const isPDF = file.type === 'application/pdf';
        const isSizeOK = file.size <= maxSizeBytes;

        if (!isPDF) {
            alert('Invalid file type. Please upload a PDF.');
            fileInput.value = '';
        } else if (!isSizeOK) {
            alert('File is too large. Maximum allowed size is 2 MB.');
            fileInput.value = '';
        }
    }
});

// Toggle "Other" input
function toggleOtherInput(select) {
    var otherInputDiv = document.getElementById("other_equipment_div");
    if (select.value == "7") {
        otherInputDiv.style.display = "block";
    } else {
        otherInputDiv.style.display = "none";
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const selected = document.getElementById("equipment_name");
    if (selected) {
        toggleOtherInput(selected);
    }
});

// Video validation & preview
document.getElementById("geo_video").addEventListener("change", function () {
    const fileInput = this;
    const file = fileInput.files[0];
    const errorMsg = document.getElementById("videoError");
    const videoPreview = document.getElementById("videoPreview");

    // Reset state
    errorMsg.classList.add("d-none");
    fileInput.classList.remove("is-invalid");
    videoPreview.classList.add("d-none");
    videoPreview.removeAttribute("src");

    if (file) {
        const maxSizeMB = 20;
        const maxSizeBytes = maxSizeMB * 1024 * 1024;

        if (file.type !== "video/mp4") {
            errorMsg.textContent = "Only MP4 video format is allowed.";
            errorMsg.classList.remove("d-none");
            fileInput.classList.add("is-invalid");
            return;
        }

        if (file.size > maxSizeBytes) {
            errorMsg.textContent = "Video size must be 20 MB or less.";
            errorMsg.classList.remove("d-none");
            fileInput.classList.add("is-invalid");
            return;
        }

        const videoURL = URL.createObjectURL(file);
        videoPreview.src = videoURL;
        videoPreview.classList.remove("d-none");
    }
});

document.getElementById("rvsfForm").addEventListener("submit", function (event) {
    const fileInput = document.getElementById("geo_video");
    const file = fileInput.files[0];
    const errorMsg = document.getElementById("videoError");

    if (file) {
        const maxSizeBytes = 20 * 1024 * 1024;
        if (file.type !== "video/mp4" || file.size > maxSizeBytes) {
            errorMsg.classList.remove("d-none");
            fileInput.classList.add("is-invalid");
            event.preventDefault();
        }
    }
});

// --- Fill latitude & longitude using browser Geolocation API ---
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

// --- File validation for MN File (PDF only, max 2MB) ---
document.addEventListener("DOMContentLoaded", function () {
    const mnFileInput = document.getElementById('id_mn_file');

    if (mnFileInput) {
        mnFileInput.addEventListener('change', function () {
            const file = this.files[0];

            if (file) {
                const maxSizeMB = 2;
                const maxSizeBytes = maxSizeMB * 1024 * 1024;

                const isPDF = file.type === 'application/pdf';
                const isSizeOK = file.size <= maxSizeBytes;

                if (!isPDF) {
                    alert('Invalid file type. Please upload a PDF.');
                    this.value = ''; // Clear invalid file
                } else if (!isSizeOK) {
                    alert('File is too large. Maximum allowed size is 2 MB.');
                    this.value = '';
                }
            }
        });
    }
});

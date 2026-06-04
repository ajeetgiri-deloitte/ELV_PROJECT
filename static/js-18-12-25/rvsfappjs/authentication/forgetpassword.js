// Wait until the DOM is fully loaded
document.addEventListener("DOMContentLoaded", function() {
    // Show loader on form submit
    const resetForm = document.getElementById("resetForm");
    const loadingOverlay = document.getElementById("loadingOverlay");

    if (resetForm && loadingOverlay) {
        resetForm.addEventListener("submit", function() {
            loadingOverlay.style.display = "flex";
        });
    }
});

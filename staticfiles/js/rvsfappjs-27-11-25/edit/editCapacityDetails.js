function toggleRemarksField() {
    const vehicleType = document.getElementById("vehicle_type_select").value;
    const remarksField = document.getElementById("remarks_field");

    if (vehicleType === "Others") {
        remarksField.style.display = "block";
    } else {
        remarksField.style.display = "none";
    }
}

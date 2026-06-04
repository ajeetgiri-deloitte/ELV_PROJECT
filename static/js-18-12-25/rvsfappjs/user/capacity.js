// --- Vehicle Multiselect Logic ---
const vehicleOptions = document.querySelectorAll('.multiselect-option');
const selectedOptionsContainer = document.getElementById('selectedOptions');
const selectedVehiclesInput = document.getElementById('selectedVehicles');
const othersContainer = document.getElementById('othersContainer');
const otherVehiclesInput = document.getElementById('otherVehicles');
const vehicleTable = document.getElementById('vehicleTable');

let selectedVehicles = [];
let alreadySavedVehicles = window.alreadySavedVehicles || []; // ✅ passed from template

// Disable already saved vehicles
vehicleOptions.forEach(option => {
    const value = option.getAttribute('data-value');
    if (alreadySavedVehicles.includes(value)) {
        option.classList.add('disabled');
        option.style.pointerEvents = "none";
        option.style.opacity = "0.4";
    }
});

updateSelectedOptions();
updateVehicleTableVisibility();

// Option click handler
vehicleOptions.forEach(option => {
    option.addEventListener('click', function() {
        const value = this.getAttribute('data-value');

        if (value === 'Others') {
            othersContainer.style.display = othersContainer.style.display === 'none' ? 'block' : 'none';
            return;
        }

        if (!selectedVehicles.includes(value) && !alreadySavedVehicles.includes(value)) {
            selectedVehicles.push(value);
            this.classList.add('selected');
            this.style.pointerEvents = "none";
            this.style.opacity = "0.5";
        }

        updateSelectedOptions();
    });
});

// Handle "Others" input
otherVehiclesInput.addEventListener('blur', function() {
    let uniqueOthers = [...new Set(
        otherVehiclesInput.value.split(',')
            .map(v => v.trim())
            .filter(v => v)
    )];
    otherVehiclesInput.value = uniqueOthers.join(', ');
    updateSelectedOptions();
});

function updateSelectedOptions() {
    selectedOptionsContainer.innerHTML = '<p><strong>Selected Vehicles:</strong></p>';

    if (selectedVehicles.length === 0 && !otherVehiclesInput.value) {
        selectedOptionsContainer.innerHTML += '<p class="text-muted">No vehicles selected</p>';
        selectedVehiclesInput.value = '';
        return;
    }

    // Selected new ones
    selectedVehicles.forEach(vehicle => {
        const optionDiv = document.createElement('div');
        optionDiv.className = 'selected-option';
        optionDiv.innerHTML = `${getVehicleDisplayName(vehicle)} <span class="remove" data-value="${vehicle}">×</span>`;
        selectedOptionsContainer.appendChild(optionDiv);
    });

    // Others input
    if (otherVehiclesInput.value) {
        const otherVehicles = [...new Set(
            otherVehiclesInput.value.split(',')
                .map(v => v.trim())
                .filter(v => v)
        )];
        otherVehicles.forEach(vehicle => {
            const optionDiv = document.createElement('div');
            optionDiv.className = 'selected-option';
            optionDiv.innerHTML = `${vehicle} (Other) <span class="remove" data-value="Other:${vehicle}">×</span>`;
            selectedOptionsContainer.appendChild(optionDiv);
        });
    }

    // Remove handler
    document.querySelectorAll('.selected-option .remove').forEach(removeBtn => {
        removeBtn.addEventListener('click', function() {
            const value = this.getAttribute('data-value');

            if (value.startsWith('Other:')) {
                const vehicleToRemove = value.substring(6);
                let otherVehicles = otherVehiclesInput.value.split(',')
                    .map(v => v.trim())
                    .filter(v => v && v !== vehicleToRemove);
                otherVehiclesInput.value = otherVehicles.join(', ');
            } else {
                selectedVehicles = selectedVehicles.filter(v => v !== value);
                const option = document.querySelector(`.multiselect-option[data-value="${value}"]`);
                if (option && !alreadySavedVehicles.includes(value)) {
                    option.classList.remove('selected');
                    option.style.pointerEvents = "auto";
                    option.style.opacity = "1";
                }
            }

            updateSelectedOptions();
        });
    });

    // Hidden input update
    const otherVehicles = otherVehiclesInput.value.split(',')
        .map(v => v.trim())
        .filter(v => v);
    const allVehicles = [...selectedVehicles, ...otherVehicles.map(v => `Other:${v}`)];
    selectedVehiclesInput.value = JSON.stringify(allVehicles);
}

function getVehicleDisplayName(value) {
    const names = {
        '2W': '2W (Two-Wheeler)',
        '3W': '3W (Three-Wheeler)',
        'LMV': 'LMV (Light Motor Vehicle)',
        'MMV': 'MMV (Medium Motor Vehicle)',
        'HMV': 'HMV (Heavy Motor Vehicle)'
    };
    return names[value] || value;
}

function updateVehicleTableVisibility() {
    vehicleTable.style.display = window.hasVehicleData ? 'block' : 'none';
}

// Validation
document.getElementById('vehicleForm').addEventListener('submit', function(e) {
    if (selectedVehicles.length === 0 && !otherVehiclesInput.value) {
        e.preventDefault();
        alert('Please select at least one vehicle type.');
    }
});

// --- Next Button Check ---
$(document).ready(function() {
    $("#nextBtn").on("click", function(e) {
        let rowCount = $("table tbody tr").length;
        if (rowCount === 0) {
            alert("Please add at least one equipment detail before proceeding.");
            e.preventDefault();
            return false;
        }
        $("#yourFormId").submit();
    });
});

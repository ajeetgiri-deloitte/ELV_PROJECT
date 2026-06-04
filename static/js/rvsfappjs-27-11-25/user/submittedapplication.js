document.addEventListener("DOMContentLoaded", () => {
    const lat = parseFloat("{{ general.latitude }}");
    const lng = parseFloat("{{ general.longitude }}");
    const unitname = "{{ entity.legal_name }}";
    const modalEl = document.getElementById('mapModal');
    let map;

    modalEl.addEventListener('shown.bs.modal', function () {
        if (!map) {
            map = L.map('mapid').setView([lat, lng], 13);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
            L.marker([lat, lng])
                .addTo(map)
                .bindPopup(unitname)
                .openPopup();
        }
        map.invalidateSize();   // Force re-calc of map layout
        map.setView([lat, lng]); // Ensure centering
    });
});

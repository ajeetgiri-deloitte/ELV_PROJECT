document.addEventListener("DOMContentLoaded", () => {
  const lat = window.mapData.lat;
  const lng = window.mapData.lng;
  const modal = document.getElementById('mapModal');
  let map;

  modal.addEventListener('shown.bs.modal', () => {
    if (!map) {
      map = L.map('mapid').setView([lat, lng], 13);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
      }).addTo(map);

      L.marker([lat, lng]).addTo(map)
        .bindPopup(`📍 (${lat.toFixed(5)}, ${lng.toFixed(5)})`).openPopup();
    }

    map.invalidateSize();
    map.setView([lat, lng]);
  });
});

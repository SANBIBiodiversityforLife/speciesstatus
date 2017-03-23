$(document).ready(function() {
  map = L.map('leaflet').setView([-29, 24.5], 5);
  var measureControl = new L.Control.Measure();
  measureControl.addTo(map);
  // Add the baselayers and vegmap overlay
  var vegmapSheet = L.esri.dynamicMapLayer({ url: 'http://bgismaps.sanbi.org/arcgis/rest/services/2012VegMap/MapServer', useCors: false, opacity: 0.5 });
  toggleLayers = { 'Vegmap sheet': vegmapSheet }
  base = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: 'Map data &copy; 2013 OpenStreetMap contributors', });
  base.addTo(map);

  // Add kml loader
  var control = L.Control.fileLayerLoad({fitBounds: true});
  control.addTo(map);
  control.loader.on('data:loaded', function (e) {

      // Add to map layer switcher
      var l = e.layer.getLayers()[0];

      $.ajax({
        url: find_distrib_url,
        data: JSON.stringify(l.toGeoJSON()),
        success: function(data, textStatus, jqXHR) {
          console.log(data);

        }
      });

      console.log(JSON.stringify(l.toGeoJSON()));
  });


});
function init_map(data) {
  map = L.map('leaflet').setView([-29, 24.5], 5);
  var measureControl = new L.Control.Measure();
  measureControl.addTo(map);
  // Add the baselayers and vegmap overlay
  var vegmapSheet = L.esri.dynamicMapLayer({ url: 'http://bgismaps.sanbi.org/arcgis/rest/services/2012VegMap/MapServer', useCors: false, opacity: 0.5 });
  base = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: 'Map data &copy; 2013 OpenStreetMap contributors', });
  base.addTo(map);
  baseMaps = { "Default": base, "Satellite imagery": L.esri.basemapLayer('Imagery') };
  L.control.layers(baseMaps, { 'Vegmap sheet': vegmapSheet }).addTo(map);

  // Change style of polygons on hover with this function
  function highlightFeature(e) {
    var layer = e.target;
    layer.openPopup();
    layer.setStyle({
      weight: 5,
      color: '#ffff99',
      dashArray: '',
      fillOpacity: 0.7
    });

    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) { layer.bringToFront(); }
  }
  function resetHighlight(e) {
    e.target.closePopup();
    s.resetStyle(e.target);
  }

  // Add geojson layer
  var s = new L.geoJson(data['results'], {
    onEachFeature: function (feature, layer) {
      area = Math.round((L.GeometryUtil.geodesicArea(layer.getLatLngs()[0]))/1000000);
      date = JSON.parse(feature.properties.date);
      popup = '<h4>' + feature.properties.residency_status  + '</h4>';
      popup += "First recorded: " + date['lower'] + ' / Area of extent: ' + area + ' km<sup>2</sup>';
      popup += "<p>" + feature.properties.description + '</p>';
      popup += "<strong>Reference:</strong><em>" + feature.properties.reference + '</em>';
      layer.bindPopup(popup);
      layer.on({
        mouseover: highlightFeature,
        mouseout: resetHighlight
      });

       item = '<tr><td>' + feature.properties.residency_status + '</td><td>' + date['lower'] +
          '</td><td>' + area + '</td><td>' + feature.properties.description + '</td><td><button class="btn btn-default pan-button" data-leaflet-id="' + feature.properties.pk + '">Pan</button></td></tr>';
       $('#places > tbody:last-child').append(item);
    },
  });
  s.addTo(map);

  //$('#places').DataTable();
}
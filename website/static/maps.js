function init_map(point_data, poly_data) {
  map = L.map('leaflet').setView([-29, 24.5], 5);
  var measureControl = new L.Control.Measure();
  measureControl.addTo(map);
  // Add the baselayers and vegmap overlay
  var vegmapSheet = L.esri.dynamicMapLayer({ url: 'http://bgismaps.sanbi.org/arcgis/rest/services/2012VegMap/MapServer', useCors: false, opacity: 0.5 });
  toggleLayers = { 'Vegmap sheet': vegmapSheet }
  base = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: 'Map data &copy; 2013 OpenStreetMap contributors', });
  base.addTo(map);
  baseMaps = { "Default": base, "Satellite imagery": L.esri.basemapLayer('Imagery') };

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
    polys.resetStyle(e.target);
  }

 console.log(poly_data['results']);
  var polys = new L.geoJson(poly_data['results'], {

    onEachFeature: function (feature, layer) {
      area = Math.round((L.GeometryUtil.geodesicArea(layer.getLatLngs()[0]))/1000000);
      popup = ' / Extent of occurrence: ' + area + ' km<sup>2</sup>'
      if(feature.properties.residency_status) {
        popup = '<h4>' + feature.properties.residency_status  + '</h4>' + popup;
      }
      if(feature.properties.date) {
        date = JSON.parse(feature.properties.date);
        popup += "First recorded: " + date['lower'];
      }
      if(feature.properties.description) {
        popup += "<p>" + feature.properties.description + '</p>';
      }
      if(feature.properties.reference) {
        popup += "<strong>Reference:</strong><em>" + feature.properties.reference + '</em>';
      }
      layer.bindPopup(popup);
      layer.on({
        mouseover: highlightFeature,
        mouseout: resetHighlight
      });

     //item = '<tr><td>' + feature.properties.residency_status + '</td><td>' + date['lower'] +
     //     '</td><td>' + area + '</td><td>' + feature.properties.description + '</td><td><button class="btn btn-default pan-button" data-leaflet-id="' + feature.properties.pk + '">Pan</button></td></tr>';
     //$('#places > tbody:last-child').append(item);
    },
  });
  polys.addTo(map);
  // map.fitBounds(polys.getBounds());
  toggleLayers['Expert opinion'] = polys;

  // Add geojson layer and create a coords list from that for the heatmap
  coords = []
  var pts = new L.geoJson(point_data, {
    onEachFeature: function (feature, layer) {
      coords.push([feature.geometry.coordinates[1], feature.geometry.coordinates[0]]);
    },
  });

  console.log(coords);
  //s.addTo(map);
  // Add heatmap
  heat = L.heatLayer(coords, {
    radius: 20,
    minOpacity: 0.3,
  }).addTo(map);
  toggleLayers['Heatmap'] = heat;

  // Add the control boxes on the map to tick things on and off
  L.control.layers(baseMaps, toggleLayers).addTo(map);
}
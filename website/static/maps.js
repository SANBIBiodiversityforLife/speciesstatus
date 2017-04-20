function init_map(point_data, poly_data) {
  map = L.map('leaflet').setView([-29, 24.5], 5);

  //setting zooming limits
  map.options.maxZoom = 7;
  map.fire('zoomend');

  // This lets people measure area and so on
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

  // Create a layer for the 'expert opinion' type polygons
  var polys = new L.geoJson(poly_data['results'], {
    onEachFeature: function (feature, layer) {
      area = Math.round((L.GeometryUtil.geodesicArea(layer.getLatLngs()[0]))/1000000);
      popup = 'Extent of occurrence: ' + area + ' km<sup>2</sup>'
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
  if(poly_data['results']['features'].length) {
    polys.addTo(map);
    map.fitBounds(polys.getBounds());
    toggleLayers['Expert opinion'] = polys;
  }

  // Add geojson layer and create a coords list from that for the heatmap
  var coords = []
  institutionCodes=[]
  var institutionCodesDict = {}
  var pts = new L.geoJson(point_data, {
    onEachFeature: function (feature, layer) {
      coords.push([feature.geometry.coordinates[1], feature.geometry.coordinates[0]]);
      var actualCode = feature.properties.origin_code.split('|')[0];
      if(!institutionCodes.includes(actualCode)) {
        institutionCodes.push(actualCode);
      }
      if(actualCode != '') {
        if(actualCode in institutionCodesDict) {
          institutionCodesDict[actualCode] = institutionCodesDict[actualCode] + 1;
        } else {
          institutionCodesDict[actualCode] = 1;
        }
      }
    },
  });
  //$('#distribution').html('<span>' + institutionCodes.join('</span><span>') + '</span>');

  var chartData = $.map(institutionCodesDict, function(v) { return v; });
  var chartLabels = $.map(institutionCodesDict, function(v, k) { return k; });
  var colours = []
  var colourIncrement = Math.floor(360/chartLabels.length);
  for(i = 0; i < chartLabels.length; i++) {
    colours.push('hsl(' + (colourIncrement * i) + ', 30%, 50%)');
  }
  var chartData = {
    type: 'doughnut',
    data: {
      datasets: [{
        data: chartData,
        backgroundColor: colours,
        label: 'Dataset 1'
      }],
      labels: chartLabels
    },
    options: {
      legend: { position: 'left',
              labels: { boxWidth: 10 } },
    }
  }
  var ctx = document.getElementById("canvas").getContext("2d");
  window.myDoughnut = new Chart(ctx, chartData);

  // Add heatmap
  heat = L.heatLayer(coords, {
    radius: 15,
    minOpacity: 0.3,
  }).addTo(map);
  toggleLayers['Heatmap'] = heat;

  // Add the control boxes on the map to tick things on and off
  L.control.layers(baseMaps, toggleLayers).addTo(map);
}
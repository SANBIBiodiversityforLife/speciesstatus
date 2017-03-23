$(document).ready(function() {
  var colorMapping = {
    "Extinct (EX)": '#000',
    "Extinct in the Wild (EW)": '#cd4444',
    "Critically Endangered (CR)": '#cd5844',
    "Endangered (EN)": '#cd7e44',
    "Vulnerable (VU)": '#cdb244',
    "Near Threatened (NT)": '#bad267',
    "Least Concern (LC)": '#d0efcc',
    "Data Deficient (DD)": '#b4b4b4',
    "Not Evaluated (NE)": '#b4b4b4'
  }
	$.ajax({
		url: chartDataUrl,
		success: function(data, textStatus, jqXHR) {
		  var stats = [];
      keys = data['names'];

      // Doing something to statistics?
      console.log(data['statistics']);
      $.each(data['statistics'], function(index, d) {
        var status = Object.keys(d)[0];
        var data_array = [];
        //keys = Object.keys(d[status]);
        keys.forEach(function(key){
            data_array.push(d[status][key]);
        });
        stats.push({label: status, data: data_array, backgroundColor: colorMapping[status]});
      });
      var label_names = [];
      $.each(data['common_names'], function(index, cn){
          label_names.push([data['names'][index], cn])
      })
      var barChartData = {
        labels: label_names,
        datasets: stats,
      };

      var ctx = document.getElementById("canvas").getContext("2d");
      window.myBar = new Chart(ctx, {
          type: 'bar',
          data: barChartData,
          options: {
              legend: { display: false },
              title: { display: false },
              tooltips: {
                  mode: 'index',
                  intersect: false
              },
              responsive: true,
              scales: {
                  xAxes: [{
                      stacked: true,
                  }],
                  yAxes: [{
                      stacked: true,
                      scaleLabel: {
                          display: true,
                          labelString: 'No. of species'
                      }
                  }]
              }
          }
      });

		}
	});
});
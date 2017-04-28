$(document).ready(function() {
  var colorMapping = {
    "Extinct (EX)": '#000',
    "Extinct in the Wild (EW)": '#cd4444',
    "Critically Endangered (CR)": '#cd5844',
    "Endangered (EN)": '#ff7f00', // cd7e44
    "Vulnerable (VU)": '#cdb244',
    "Near Threatened (NT)": '#bce400', // bad267
    "Least Concern (LC)": '#d1ecff',
    "Data Deficient (DD)": '#b4b4b4',
    "Not Evaluated (NE)": '#b4b4b4'
  }
	$.ajax({
		url: chartDataUrl,
		success: function(data, textStatus, jqXHR) {
		  var stats = [];
      keys = data['names'];

      // Doing something to statistics?
      $.each(data['statistics'], function(index, d) {
        var status = Object.keys(d)[0];
        var data_array = [];
        //keys = Object.keys(d[status]);
        keys.forEach(function(key){
            data_array.push(d[status][key]);
        });
        stats.push({label: status, data: data_array, backgroundColor: colorMapping[status], hoverBackgroundColor: colorMapping[status]});
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


      var ctx = document.getElementById('land').getContext('2d');
      new Chart(ctx, {
        type: 'pie',
        data: {
            labels: [
                "South Africa",
                "Rest of World",
            ],
            datasets: [
                {
                    data: [2, 98],
                    backgroundColor: [
                        "#888",
                        "#DDD",
                    ],
                    hoverBackgroundColor: [
                        "#888",
                        "#DDD",
                    ]
                }]
        },
        options: {
            animation:{
                animateScale:true
            },
            legend: { display: false }
        }
      });

      var ctx = document.getElementById('plant').getContext('2d');
      new Chart(ctx, {
        type: 'pie',
        data: {
            labels: [
                "South Africa",
                "Rest of World",
            ],
            datasets: [
                {
                    data: [10, 90],
                    backgroundColor: [
                        "#80c615",
                        "#c8cec0",
                    ],
                    hoverBackgroundColor: [
                        "#80c615",
                        "#c8cec0",
                    ]
                }]
        },
        options: {
            animation:{
                animateScale:true
            },
            legend: { display: false }
        }
      });

      var ctx = document.getElementById('terrestrial').getContext('2d');
      new Chart(ctx, {
        type: 'pie',
        data: {
            labels: [
                "South Africa",
                "Rest of World",
            ],
            datasets: [
                {
                    data: [7, 93],
                    backgroundColor: [
                        "#FF3158",
                        "#dbc5c9",
                    ],
                    hoverBackgroundColor: [
                        "#FF3158",
                        "#dbc5c9",
                    ]
                }]
        },
        options: {
            animation:{
                animateScale:true
            },
            legend: { display: false }
        }
      });

      var ctx = document.getElementById('marine').getContext('2d');
      new Chart(ctx, {
        type: 'pie',
        data: {
            labels: [
                "South Africa",
                "Rest of World",
            ],
            datasets: [
                {
                    data: [15, 85],
                    backgroundColor: [
                        "#3187F8",
                        "#94afd3",
                    ],
                    hoverBackgroundColor: [
                        "#3187F8",
                        "#94afd3",
                    ]
                }]
        },
        options: {
            animation:{
                animateScale:true
            },
            legend: { display: false }
        }
      });
		}
	});
});
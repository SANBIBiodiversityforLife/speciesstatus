
function populate_categories(category_url) {
  // This is hardcoded, we should probably hook it into the API
  var redlist_categories = ['LC', 'NT', 'VU', 'EN', 'CR', 'EW', 'EX', 'DD', 'NE']
  var redlist_categories_long = ['Least concern', 'Near threatened', 'Vulnerable', 'Endangered', 'Critically endangered', 'Extinct in the wild', 'Extinct', 'Data deficient', 'Not evaluated'];

  top_html = []
  for(i = 0; i < redlist_categories.length; i++) {
    html = '<a data-href="' + categoryListUrl.replace('LC', redlist_categories[i]) + '" class="assessment assessment-' + redlist_categories[i] + '">';
    html += redlist_categories_long[i] + '</a>';
    top_html.push(html);
  }
  $('#redlistcat').html('<div id="redlist-cat-headings">' + top_html.join(' ') + '</div><hr>');
  $('#redlistcat a').click(function() {
    populate_categories($(this).attr('data-href'));
  });

  $.ajax({
    url: category_url,
    success: function(data, textStatus, jqXHR) {
      var page_no = data['count']/10;
      var pagination = generatePagination(page_no, category_url)

      if(data['results'].length == 0){
        $('#redlistcat').append('<p><em>No results</em></p>');
      } else {
        var content = '';
        $.each(data['results'], function(index, value) {
          content += '<p><a href="' + taxaDetailUrl.replace('0', value['id']) + '">'+ value['name'] + '</a>';
          if(value['get_top_common_name']) {
            content += ' - ' + value['get_top_common_name']
          }
          content += ' (' + value['rank']['name'] + ')';
          if(value['get_latest_assessment']) {
            content += ' <span class="assessment assessment-' + value['get_latest_assessment'] + '">' + value['get_latest_assessment'] + '</span>';
          }
          content += '</p>';
        });
        $('#redlistcat').append(content + '<hr>' + pagination);

        $('#redlistcat .pagination a').click(function() {
          populate_categories($(this).attr('data-letter-href'));
        });
      }
    }
  });
}

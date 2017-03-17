var alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXY'.split('');
var alphabet_html = [];
$.each(alphabet, function(index, value) {
  alphabet_html.push('<a href="#" data-href="' + generaAZUrl.replace('A', value) + '">' + value + '</a>');
});


function populate_genera(letter_url) {
  $('#azgenera').html('<div id="generaAZList">' + alphabet_html.join(' | ') + '</div><hr>');
  $('#generaAZList a').click(function() {
    populate_genera($(this).attr('data-href'));
  });

  $.ajax({
    url: letter_url,
    success: function(data, textStatus, jqXHR) {
      var page_no = data['count']/10;
      var pagination = '<nav aria-label="Page navigation"><ul class="pagination">';
      for(i = 1; i < page_no; i++) {
        pagination += '<li><a href="#">' + i + '</a></li>';
      }
      pagination += '</ul></nav>';

      if(data['results'].length == 0){
        $('#azgenera').append('<p><em>No results</em></p>');
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
        $('#azgenera').append(content + '<hr>' + pagination);
      }
    }
  });
}

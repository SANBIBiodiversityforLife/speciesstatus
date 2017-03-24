var alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXY'.split('');
var alphabet_html = [];
$.each(alphabet, function(index, value) {
  alphabet_html.push('<a href="#" data-letter-href="' + generaAZUrl.replace('A', value) + '">' + value + '</a>');
});

$.ajax({
  url: taxaGroupList,
  success: function(data, textStatus, jqXHR) {
    var html = '<div id="generaClassList">';
    $.each(data, function(index, group_name) {
      if(group_name == 'Aves') {
        html += '<a class="btn btn-default btn-warning" href="#" role="button">' + group_name + '</a> ';
      } else {
        html += '<a class="btn btn-default" href="#" role="button">' + group_name + '</a> ';
      }
    });
    html += '</div><hr>';
    $('#azgenera').html(html);

    // Whenever a taxonomic group is clicked, make sure we change the URL of the letters
    $('#generaClassList a').click(function() {
      var val = $(this).html();
      $('#generaAZList a').attr('data-letter-href', function() {
        var parts = $(this).attr('data-letter-href').split('/')
        var previous = parts.pop();
        var previous = parts.pop();
        return $(this).attr('data-letter-href').replace(previous, val);
      });
      $(this).parent().children('a').removeClass('btn-warning');
      $(this).addClass('btn-warning');
      populate_genera($('#generaAZList a').first().attr('data-letter-href'));
      //$('#generaAZList a').attr('data-taxa', val);
    });

    // Print out the other HTML
    $('#azgenera').append('<div id="generaAZList">' + alphabet_html.join(' | ') + '</div><hr>');
    $('#generaAZList a').click(function() {
      populate_genera($(this).attr('data-letter-href'));
    });
    $('#azgenera').append('<div id="generaResults"></div>');
  }
  });



function populate_genera(letter_url) {
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
        $('#generaResults').html('<p><em>No results</em></p>');
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
        $('#generaResults').html(content + '<hr>' + pagination);
      }
    }
  });
}

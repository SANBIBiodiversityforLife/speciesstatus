var alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXY'.split('');
var alphabet_html = [];
$.each(alphabet, function(index, value) {
  alphabet_html.push('<a href="#" data-letter-href="' + change_url_letter(generaAZUrl, value) + '">' + value + '</a>');
});

function change_url_letter(url, new_letter) {
  var urlParts = url.split('/');
  // Sanity check
  if(urlParts[urlParts.length - 2].length == 1) {
    urlParts[urlParts.length - 2] = new_letter;
  }
  return urlParts.join('/');
}

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
        var previous = parts[parts.length - 3];
        return $(this).attr('data-letter-href').replace(previous, val);
      });
      $(this).parent().children('a').removeClass('btn-warning');
      $(this).addClass('btn-warning');
      populate_genera($('#generaAZList a').first().attr('data-letter-href'));
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
      var page_no = Math.ceil(data['count']/20);
      var pagination = '<nav aria-label="Page navigation"><ul class="pagination">';
      if(page_no > 1) {
        for(i = 1; i <= page_no; i++) {
          var pagination_url = letter_url;
          if(pagination_url.indexOf('page=') >= 0) {
            pagination_url = pagination_url.replace(/page=\d/, 'page=' + i);
          } else {
            pagination_url += '&page=' + i;
          }
          pagination += '<li><a href="#" data-letter-href="' + pagination_url + '">' + i + '</a></li>';
        }
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

        $('.pagination a').click(function() {
          populate_genera($(this).attr('data-letter-href'));
        });
      }
    }
  });
}

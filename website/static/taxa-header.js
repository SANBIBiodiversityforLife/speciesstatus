$(document).ready(function() {
  // Retrieve species image if possible
  $.ajax({
    url: '/taxa/get-images/' + id + '/?format=json',
    success: function(data, textStatus, jqXHR) {
      if(data != 0) {
        $('#taxon-img-container img').attr('src', '/static/' + data['thumb']);
        $('#taxon-img-container a').attr('href', '/static/' + data['file']);
        $('#taxon-img-container a').attr('data-title', 'Photographer: ' + data['author']);
        $('#taxon-img-container a').attr('data-footer', '&copy; ' + data['copyright']);
        //$('#taxon-img-container a').attr('data-remote', '/static/' + data['file']);

        $('#imgphotographer').append(data['author']);
        $('#imgcopyright').append(data['copyright']);
        //$('#taxon-img-container').show();
        $('#taxon-img-container').css('width', '200px');
        $('#taxon-img-container img').hover(function() { $('#taxon-img-container div').show('fast'); },
                                            function() { $('#taxon-img-container div').hide('fast'); });
      } else {
        $('#taxon-img-container').hide();
      }
      console.log(data);
      console.log(textStatus);
    }
  });



  // Replace all nav with correct urls
  $('.nav-tabs a').each(function(index, ele) { $(ele).attr('href', $(ele).attr('href').replace('0', id)); });

  $.ajax({
    url: ancestors_url,
    success: function(data, textStatus, jqXHR) {
      $.each(data, function(index, ancestor) {
        if(index != 0) {
          $('#breadcrumb').append(' <span class="glyphicon glyphicon-menu-right" aria-hidden="true"></span> ');
        }
        $('#breadcrumb').append('<a href="' + lineage_url.replace('0', ancestor.id) + '" data-toggle="tooltip" data-placement="top" title="' + ancestor.rank.name + '">' + ancestor.name + '</a>');

        if(index == data.length - 1) {
          $('#breadcrumb').append(' <a href="' + lineage_url.replace('0', ancestor.id) + '" type="button" class="btn btn-warning btn-sm">View tree</a>')
          $('h1').append(ancestor.get_full_name);
        }
      });
    }
  }).done(function() {
    $.ajax({
      url: common_names_url,
      success: function(data, textStatus, jqXHR) {
        $.each(data.results, function(index, common_name) {
            $('#common-names').append('<span data-toggle="tooltip" data-placement="top" title="' + common_name.language + '">' + common_name.name + '</span>');
        });
      }
    }).done(function() {
      // We are nesting all of these dones just so that trianglify can get the right height for his bg
      var params = {
        height: $('.triangles').outerHeight(),
        width: $('.triangles').outerWidth(),
        x_colors: 'Blues',
        y_colors: 'match_x'
      };
      var pattern = new Trianglify(params);
      $('.triangles').attr('style', 'background: url(' + pattern.png() + ') no-repeat center center');

      // Toggle bootstrap tooltips
      $('[data-toggle="tooltip"]').tooltip();
    });
  });
});
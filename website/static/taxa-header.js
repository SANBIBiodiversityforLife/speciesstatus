$(document).ready(function() {
  // Fix the image width
  $('#taxon-img-container img').addClass(function( index ) {
    return (this.width/this.height > 1) ? 'img-wide' : 'img-tall';
  })

  // Find/replace all the underscores
  function replaceFunction(index, html) {
    return html.replace(/_(narrative)?/g, '');
  }
  $('#species-info').html(replaceFunction);
  $('#redlist-summary').html(replaceFunction);

  // Retrieve species image if possible
  $.ajax({
    url: '/taxa/get-images/' + id + '/?format=json',
    success: function(all_data, textStatus, jqXHR) {
      if(all_data != 0) {
        // The initial image gets added, it's the thumbnail which people click to view other images
        var data = all_data.shift();
        $('#taxon-img-container img').attr('src', '/static/' + data['file']); // thumb should go here
        $('#taxon-img-container a').attr('href', '/static/' + data['file']);

        // Add all of the data attributes which will show up on the slideshow
        $('#taxon-img-container a').attr('data-title', 'Photographer: ' + data['author'] + ' ( - Image 1 of ' + (all_data.length + 1) + ')');
        if(data['source']) {
          $('#taxon-img-container a').attr('data-footer', '&copy; ' + data['copyright'] + ' - Source: ' + data['source']);
        } else {
          $('#taxon-img-container a').attr('data-footer', '&copy; ' + data['copyright']);
        }

        // This will appear on hover over the image
        $('#imgphotographer').append(data['author']);
        $('#imgcopyright').append(data['copyright']);

        // Next expand the image container (seeing as the img exists), we can't show/hide bcos it screws up the automatically generated triangular pattern
        //$('#taxon-img-container div').css('width', '200px');
        $('#taxon-img-container div').addClass('img-container-width');
        $('#taxon-img-container').css('border-width', '10px');
        //$('#taxon-img-container img').hover(function() { $('#taxon-img-container div').show('fast'); $('#taxon-img-container p').hide('fast'); },
        //                                    function() { $('#taxon-img-container div').hide('fast'); $('#taxon-img-container p').show('fast'); });

        // Loop over the other images and add them to the hidden image gallery div so people can scroll through them
        $.each(all_data, function(index, data) {
          var html = '<a href="/static/' + data['file'] + '" data-toggle="lightbox" data-gallery="species-gallery" ';
          html += 'data-title="Photographer: ' + data['author'] + ' ( - Image ' + (index + 2) + ' of ' + (all_data.length + 1) + ') "';
          if(data['source']) {
            html += 'data-footer="&copy; ' + data['copyright'] + ' - Source: ' + data['source'] + '">';
          } else {
            html += 'data-footer="&copy; ' + data['copyright'] + '">';
          }
          html += '<img src="/static/' + data['file'] + '"></a>';
          $('#img-gallery').append(html);
        });
      } else {
        $('#taxon-img-container').hide();
      }
    }
  });



  // Replace all nav with correct urls
  $('.nav-tabs a').each(function(index, ele) { $(ele).attr('href', $(ele).attr('href').replace('0', id)); });

  $.ajax({
    url: ancestors_url,
    success: function(data, textStatus, jqXHR) {
      $.each(data, function(index, ancestor) {
        var start_index = 2;
        if(index < start_index) {
          return true; // Note this is the same as continue in python
        }
        if(index != start_index) {
          $('#breadcrumb').append(' <span class="glyphicon glyphicon-menu-right" aria-hidden="true"></span> ');
        }
        $('#breadcrumb').append('<a href="' + lineage_url.replace('0', ancestor.id) + '" data-toggle="tooltip" data-placement="top" title="' + ancestor.rank.name + '">' + ancestor.name + '</a>');

        if(index == data.length - 1) {
          $('#breadcrumb').append(' <a href="' + lineage_url.replace('0', ancestor.id) + '" type="button" class="btn btn-warning btn-sm">View tree</a>')
          //$('h1').append(ancestor.get_full_name);
        }

      });
    }
  }).done(function() {
    // Insert the logos into the page. We have to have this in here because this is how we find out the ancestors of a page
    if($('#redlist-summary').length) { insertLogos(); }

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
      //$('.triangles').attr('style', 'background: url(' + pattern.png() + ') no-repeat center center');

      // Toggle bootstrap tooltips
      $('[data-toggle="tooltip"]').tooltip();
    });
  });
});
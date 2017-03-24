$(document).ready(function() {
	$("#search").autocomplete({
    source: function(request, response) {
      $.ajax({
        url: searchAutoCompleteUrl,
        dataType: "json",
        data: {
          search: request.term
        },
        success: function (data) {
          response($.map(data.results, function (item) {
            label_text = item.name;
            if(item['get_top_common_name']) {
              label_text += ' (' + item['get_top_common_name'] + ')'
            }
            if(item['get_latest_assessment']) {
              label_text += ' <span class="assessment assessment-' + item['get_latest_assessment'] + '">' + item['get_latest_assessment'] + '</span>';
            }
            return {
              label: label_text,
              value: item.id
            };
          }));
        }
      });
    },
    minLength: 3,
		select: function(event, ui) {
		  location.href = searchRedirectUrl.replace('0', ui.item.value);
      return false;
		},
  }).data("ui-autocomplete")._renderItem = function( ul, item ) {
    return $('<li style="margin-top: 7px; margin-bottom: 7px;"></li>')
      .data( "item.autocomplete", item )
      .append( '<a>'+ item.label + "</a>" )
      .appendTo( ul );
  };
});
$(document).ready(function() {
	$("#searchterm").autocomplete({
    source: function(request, response) {
      $.ajax({
        url: searchAutoCompleteUrl,
        dataType: "json",
        data: {
          search: request.term
        },
        success: function (data) {
          response($.map(data.results, function (item) {
            return {
              label: item.name + ' (' + item.get_top_common_name + ')',
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
  });
});
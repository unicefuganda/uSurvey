;
jQuery(function($){
  function next_element(element) {
    return element.parent().next().find('select');
  }

  function previous_element(element) {
    return element.parent().prev().find('select');
  }

  function populate_children(element, data) {
    element.trigger('clear-locations');
    var option;
    $.each(data, function(){
      option = $('<option data-location=true/>').val(this.id).text(this.name);
      element.append(option);
    });
    element.trigger("liszt:updated");
  }

  var location = $('input[name=location]');

  $("#location-widget select")
        .on('change', function(){
            var element = $(this),
                value = element.val(),
                url = "/location/" + value + "/children";
            if($.isEmptyObject(value)){
              value = previous_element(element).val();
              location.val(value);
              next_element(element).trigger('clear-locations');
              return true;
            }
            location.val(value);
            $.getJSON(url, function(data){
              populate_children(next_element(element), data);
            });
        })
        .on('clear-locations', function(){
            var element = $(this);
            element.find('option[data-location=true]').remove();
            element.trigger("liszt:updated");
            next_element(element).trigger('clear-locations');
        });

  location.val($("#location-widget option[selected]").last().val());
});
;
jQuery(function($){
  function get_next_element(element) {
    return element.parents(".parent").next().find('select');
  }

  function get_previous_element(element) {
    return element.parents(".parent").prev().find('select');
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
                url = "/location/" + value + "/children",
                next_element = get_next_element(element);
            if($.isEmptyObject(value)){
              value = get_previous_element(element).val();
              location.val(value);
              next_element.trigger('clear-locations');
              return true;
            }
            if(next_element.length > 0){
              location.val(value);
              $.getJSON(url, function(data){
                populate_children(next_element, data);
              });
            } else{
              location.val(value)
              $(document).trigger('location-selected');
            };
        })
        .on('clear-locations', function(){
            var element = $(this);
            element.find('option[data-location=true]').remove();
            element.trigger("liszt:updated");
            get_next_element(element).trigger('clear-locations');
        });

  location.val($("#location-widget option[selected]").last().val()).trigger('change');
});
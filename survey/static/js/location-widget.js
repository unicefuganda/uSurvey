;
jQuery(function($){

    function getNextElement(element) {
        return element.parents(".parent").next().find('select');
    }

    function getPreviousElement(element) {
        return element.parents(".parent").prev().find('select');
    }

    function populateChildren(element, data) {
        element.trigger('clear-locations');
        var option;
        $.each(data, function(){
        option = $('<option data-location=true/>').val(this.id).text(this.name);
        element.append(option);
        });
        element.trigger("liszt:updated");
    }

    function clearOptions(element){
        element.find('option[data-location=true]').remove();
        element.trigger("liszt:updated");
    }

    function populateEA(value){
        var url = "/locations/" + value + "/enumeration_areas";
        $.getJSON(url, function(data){
            clearOptions($ea)
            var option;
            $.each(data, function(){
                option = $('<option data-location=true/>').val(this.id).text(this.name);
                $ea.append(option);
            });
            $ea.trigger("liszt:updated");
        });
    }

  var location = $('input[name=location]'),
      $ea = $('#widget_ea');


  $("#location-widget select")
        .on('change', function(){
            var element = $(this),
                value = element.val(),
                url = "/locations/" + value + "/children",
                next_element = getNextElement(element);

            if($.isEmptyObject(value)){
              value = getPreviousElement(element).val();
              next_element.trigger('clear-locations');
              clearOptions($ea)
              location.val(value)
              return true;
            }

            if(next_element.length > 0){
              $.getJSON(url, function(data){
                populateChildren(next_element, data);
                location.val(value)
              });
            } else{
              populateEA(value);
              location.val(value)
            }
        })
      .on('clear-locations', function(){
            var element = $(this);
            clearOptions(element)
            getNextElement(element).trigger('clear-locations');
        });

  location.val($("#location-widget option[selected]").last().val());

  $("#widget_ea").on('change', function(){
      $(document).trigger('location-selected');
      $('input[name=ea]').val($(this).val());
  });

});

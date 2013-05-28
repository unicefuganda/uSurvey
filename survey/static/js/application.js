;

$(function(){
  var loaded_locations,
      location_value = $('input[name=location]');
  $("#investigator-location").typeahead({
    minLength: 4,
    source: function (query, process) {
      $.getJSON('/investigators/locations', {q: query}, function(data){
        loaded_locations = data;
        process(_.keys(data))
      })
    },
    updater: function(location){
      location_value.val(loaded_locations[location]);
      return location;
    }
  })

  jQuery.validator.addMethod("dependentField", function(value, element) {
    var e = $(element);
    return !(_($(e.attr('data-dependent')).val()).isEmpty());
  }, "This field is required");

  $('.investigator-form').validate({
      rules: {
        "name": "required",
        "mobile_number": {
          required: true,
          remote: '/investigators/check_mobile_number'
        },
        "age": "required",
        "location-name":{
          required: true,
          dependentField: true
        }
      },
      messages: {
        "mobile_number": {
          remote: jQuery.format("{0} is already registered.")
        }
      },
      submitHandler: function(form, e){
        e.preventDefault()
        form = $(form);
        var button = form.find('button'),
            value = button.val();
        button.attr('disabled', true);
        $.post(form.attr('action'), form.serializeArray(), function(data){
          window.location.href = $("#next-page").val();
        })
        return false;
      }
  });

});
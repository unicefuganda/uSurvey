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
        "mobile_number": "required",
        "age": "required",
        "location-name":{
          required: true,
          dependentField: true
        }
      },
      submitHandler: function(form, e){
        e.preventDefault()
        form = $(form);
        $.post(form.attr('action'), form.serializeArray(), function(data){
          console.log(data);
        })
        return false;
      }
  });

});
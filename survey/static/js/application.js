;

function populate_location_typeahead(location_type, parent_id){
  var loaded_locations,
      location_value = $('input[name=location]');
  $(location_type.id_name).typeahead({
    minLength: 4,
    source: function (query, process) {
      $.getJSON('/investigators/locations', {q: query, parent: parent_id}, function(data){
        loaded_locations = data;
        process(_.keys(data))
        })
      },
      updater: function(location){
        if (location_type.child){
          populate_location_typeahead(location_type.child, loaded_locations[location]);
        }
        else {
          location_value.val(loaded_locations[location]);
        }  
        return location;
      }
    })
}

var village = {id_name:"#investigator-village"};
var parish = {id_name:"#investigator-parish", child: village};
var subcounty = {id_name:"#investigator-subcounty", child: parish};
var county = {id_name:"#investigator-county", child: subcounty};
 

$(function(){
  var loaded_locations
  $("#investigator-district").typeahead({
    minLength: 4,
    source: function (query, process) {
      $.getJSON('/investigators/locations', {q: query}, function(data){
        loaded_locations = data;
        process(_.keys(data))
        })
      },
      updater: function(location){
        populate_location_typeahead(county, loaded_locations[location])
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


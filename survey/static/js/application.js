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
});
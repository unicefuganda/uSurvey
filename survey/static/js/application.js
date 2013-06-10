;

$(".chzn-select").chosen();

function populate_location_chosen(location_type, parent_id){
  $.getJSON('/investigators/locations', {parent: parent_id}, function(data) {
      $.each(data, function(key, value) {   
           $(location_type)
                .append($('<option>')
                .val(value)
                .text(key)); 
      });
      
      $(location_type).trigger("liszt:updated");
      
    });
};

function update_location_list(parent, child){
  $(parent).chosen().change( function(){
       populate_location_chosen(child, $(parent).val());
     });
};

$(function(){

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
  
  populate_location_chosen('#investigator-district');
  update_location_list('#investigator-district', '#investigator-county');
  update_location_list('#investigator-county', '#investigator-subcounty');
  update_location_list('#investigator-subcounty', '#investigator-parish');
  update_location_list('#investigator-parish', '#investigator-village');
  
  $('#investigator-village').chosen().change( function(){
       $("#location-value").val($("#investigator-village").val());
     });
  
});


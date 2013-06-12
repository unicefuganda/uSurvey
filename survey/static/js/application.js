;

$(".chzn-select").chosen();

function populate_location_chosen(location_type, parent_id){
  $.getJSON('/investigators/locations', {parent: parent_id}, function(data) {     
      $.each(data, function(key, value) {   
           $(location_type.id_name)
                .append($('<option>')
                .val(value)
                .text(key)); 
      });
      
  $(location_type.id_name).trigger("liszt:updated");
  });
};

function notify(location_type){
  $(location_type.id_name)
      .find('option')
      .remove()
      .end()
      .append('<option value=""></option>');
      
  $(location_type.id_name).trigger("liszt:updated");

  if (location_type.child){
    notify(location_type.child);    
  };
  
};

function update_location_list(location_type){
  $(location_type.id_name).chosen().change( function(){
       populate_location_chosen(location_type.child, $(location_type.id_name).val());
       
       $("#a-investigator-list").attr("href", "/investigators/?parent="+$(location_type.id_name).val())
       
       if (location_type.child){
         notify(location_type.child);    
       };
       
     });
};


var village = {'id_name': '#investigator-village'};
var parish = {'id_name': '#investigator-parish', 'child': village};
var subcounty = {'id_name': '#investigator-subcounty', 'child': parish};
var county = {'id_name': '#investigator-county', 'child': subcounty};
var district = {'id_name': '#investigator-district', 'child': county};

$(function(){
  
  jQuery.validator.addMethod("mobile_number_length", function(value, element) {
      return (value.length==9)
    }, "Please enter 9 numbers");

  jQuery.validator.addMethod("no_leading_zero", function(value, element) {
      return !(value[0]==0)
    }, "No leading zero. Please follow format.");
  
  $('.investigator-form').validate({
      ignore: ":hidden:not(select)",
      rules: {
        "name": "required",
        "mobile_number": {
          required: true,
          mobile_number_length: true,
          no_leading_zero: true,
          remote: '/investigators/check_mobile_number'
        },
        "age": "required",
        "district":"required",
        "county":"required",
        "subcounty":"required",
        "parish":"required",                        
        "village":"required"
      },
      messages: {
        "mobile_number": {
          remote: jQuery.format("{0} is already registered.")
        }
      },
      errorPlacement: function(error, element) {
        if ($(element).is(':hidden')) {
          error.insertAfter(element.next());
        } else {
          error.insertAfter(element);
        };
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
  
  populate_location_chosen(district);
  update_location_list(district);
  update_location_list(county);
  update_location_list(subcounty);
  update_location_list(parish);
  
  $('#investigator-village').chosen().change( function(){
       $("#location-value").val($("#investigator-village").val());
     });     
});

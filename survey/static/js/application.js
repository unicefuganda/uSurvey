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

function update_get_investigator_list_link(id){
  $("#a-investigator-list").attr("href", "/investigators/filter/"+id +"/");
};  

function update_location_list(location_type){
  $(location_type.id_name).chosen().change( function(){
       populate_location_chosen(location_type.child, $(location_type.id_name).val());
       
       update_get_investigator_list_link($(location_type.id_name).val())
       
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

function clean_number(value){
  return value.replace(/\s+/g, '').replace(/-/g, '');
};

function strip_leading_zero(element){
  var value = $(element).val();
  $(element).val(value.replace(/^[0]/g,""));
  return true;
};


$(function(){
  
  jQuery.validator.addMethod("leading_zero_if_number_is_10_digits", function(value, element) {
      return ((value.length !=10) || (value[0]==0) )
    }, "The first digit should be 0 if you enter 10 digits.");

  jQuery.validator.addMethod("no_leading_zero_if_number_is_9_digits", function(value, element) {
      return ( (value.length !=9) || (value[0] !=0))
    }, "No leading zero. Please follow format: 791234567.");
  
  jQuery.validator.addMethod("validate_confirm_number", function(value, element) {
        var cleaned_original = clean_number($("#investigator-mobile-number").val());
        var cleaned_confirm = clean_number(value);
        return (cleaned_original==cleaned_confirm)
      }, "Mobile number not matched.");
  
  $('.investigator-form').validate({
      ignore: ":hidden:not(select)",
      rules: {
        "name": "required",
        "mobile_number": {
          required: true,
          minlength: 9,
          maxlength:10,
          no_leading_zero_if_number_is_9_digits: true,
          leading_zero_if_number_is_10_digits: true,
          remote: '/investigators/check_mobile_number'
        },
        "confirm-mobile_number":{validate_confirm_number: true, required: true},
        "age": "required",
        "district":"required",
        "county":"required",
        "subcounty":"required",
        "parish":"required",                        
        "village":"required"
      },
      messages: {
        "mobile_number": {
          minlength:jQuery.format("Too few digits. Please enter {0} digits."),
          maxlength:jQuery.format("Too many digits. Please enter {0} digits."),
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
        strip_leading_zero("#investigator-mobile-number");
        var button = form.find('button'),
            value = button.val();
        button.attr('disabled', true);
        $.post(form.attr('action'), form.serializeArray(), function(data){
          window.location.href = $("#next-page").val();
        })
        return false;
      }
  });
  
  $("#confirm-investigator-number").on('paste', function(e) {
    e.preventDefault();
  });
  
  populate_location_chosen(district);
  update_location_list(district);
  update_location_list(county);
  update_location_list(subcounty);
  update_location_list(parish);
  
  $('#investigator-village').chosen().change( function(){
       $("#location-value").val($("#investigator-village").val());
       update_get_investigator_list_link($('#investigator-village').val())
   });     
});

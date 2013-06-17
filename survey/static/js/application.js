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
  var reset_option_text = '';
  if($(location_type.id_name).attr('data-placeholder')=='All'){
    reset_option_text = 'All';
  }
  $(location_type.id_name)
      .find('option')
      .remove()
      .end()
      .append('<option value="">'+ reset_option_text +'</option>');
      
  $(location_type.id_name).trigger("liszt:updated");

  if (location_type.child){
    notify(location_type.child);    
  };
  
};

function update_get_investigator_list_link(id){
  filter_id = ""
  if (id){
    filter_id = "filter/"+ id +"/"
  }
  $("#a-investigator-list").attr("href", "/investigators/"+ filter_id);
};  

function update_location_list(location_type){
  $(location_type.id_name).chosen().change( function(){
       var location_value = $(location_type.id_name).val();
       if (location_value && location_type.child){
         populate_location_chosen(location_type.child, location_value);
         update_get_investigator_list_link($(location_type.id_name).val())
        } else{
          var parent = location_type.location_parent;
          update_get_investigator_list_link($(parent.id_name).val())
        }
       
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
village.location_parent=parish;
parish.location_parent=subcounty;
subcounty.location_parent=county;
county.location_parent=district;
district.location_parent=district;


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
    }, "No leading zero. Please follow format: 771234567.");
  
  jQuery.validator.addMethod("validate_confirm_number", function(value, element) {
        var cleaned_original = clean_number($("#investigator-mobile_number").val());
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
          no_leading_zero_if_number_is_9_digits: true,
          leading_zero_if_number_is_10_digits: true,
          remote: '/investigators/check_mobile_number'
        },
        "confirm_mobile_number":{validate_confirm_number: true, required: true},
        "age": "required",
        "district":"required",
        "county":"required",
        "subcounty":"required",
        "parish":"required",                        
        "village":"required"
      },
      messages: {
        "age":{number: "Please enter a valid number. No space or special charcters."},
        "mobile_number": {
          number: "Please enter a valid number. No space or special charcters.",
          minlength:jQuery.format("Too few digits. Please enter {0} digits."),
          remote: jQuery.format("{0} is already registered.")
        },
        "confirm_mobile_number":{number: "Please enter a valid number. No space or special charcters"}
      },
      errorPlacement: function(error, element) {
        if ($(element).is(':hidden')) {
          error.insertAfter(element.next());
        } else {
          error.insertAfter(element);
        };
       },
      submitHandler: function(form){
         strip_leading_zero("#investigator-mobile_number");
         strip_leading_zero("#investigator-confirm_mobile_number");
         var button = $(form).find('button'),
             value = button.val();
         button.attr('disabled', true);
         form.submit();
       }
  });
  
  $("#investigator-confirm_mobile_number").on('paste', function(e) {
    e.preventDefault();
  });
  
  // $("select[data-location=true]").each(function(){
  //   update_location_list($(this));
  // });
  
  update_location_list(district);
  update_location_list(county);
  update_location_list(subcounty);
  update_location_list(parish);
  
  $('#investigator-village').chosen().change( function(){
       var location_value = $("#investigator-village").val()
       $("#investigator-location").val(location_value);
       update_get_investigator_list_link(location_value)
   });     
});

;

jQuery(function($){
  $(".chzn-select").chosen();
  $("#bulk-sms-locations").multiSelect();
});

function clean_number(value){
  return value.replace(/\s+/g, '').replace(/-/g, '');
};

function strip_leading_zero(element){
  var value = $(element).val();
  if (value){
    $(element).val(value.replace(/^[0]/g,""));
    return true;
  };
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

});

function disable_selected(identifier){
    $.each( $(identifier + "[type=number]"), function(){
          $(this).val(0);
          $(this).attr("disabled", true);
      });
};

function enable_selected(identifier){
    $.each( $(identifier+"[type=number]"), function(){
          $(this).removeAttr('disabled');
      });
};

function chosen_automatic_update(given_id, hidden_id){
    $(given_id).trigger("liszt:updated").chosen().change(function(){
        $(hidden_id).val($(this).val());

    });
};
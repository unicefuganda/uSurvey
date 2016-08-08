
;

jQuery(function($){
var occupation = $('#household-occupation'),
      other_occupation = occupation.find('option:last').val();
  function append_extra_occupation_field(){
    if(occupation.val() == other_occupation){
      occupation.after("<input name='occupation' max_length=50 id='extra-occupation-field' Placeholder='Specify' type='text'/>");
      $("#extra-occupation-field").rules('add', {required:true});
    };
  };

  append_extra_occupation_field();
  occupation.change(function(){
    if(occupation.val() != other_occupation){
      $('#extra-occupation-field').remove();
    }else{
      append_extra_occupation_field();
    }
  });

  $('#household-extra_resident_since_month').on('change', function(){
    $('#household-resident_since_month').val($(this).val());
  });

  $('#household-extra_resident_since_year').on('change', function(){
        $('#household-resident_since_year').val($(this).val());
    });

});
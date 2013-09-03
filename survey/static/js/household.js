;

jQuery(function($){
  $('#create-household-form').validate({
      ignore: ':hidden:not(select)',
      rules: {
        'age': 'required',
        'surname':'required',
        'first_name':'required',
        'occupation':'required',
      },
      messages: {
        'age':{ number: 'Please enter a valid number. No space or special charcters.'},
      },
      errorPlacement: function(error, element) {
        if ($(element).is(':hidden')) {
          error.insertAfter(element.next());
        } else {
          error.insertAfter(element);
        };
       }
  });

  $(document).on('location-selected', function(){
    var location = $('input[name=location]').val();
    $.getJSON('/households/investigators', {'location':location}, function(data){
      $.each(data, function(key, value) {
        $('#household-investigator').append($('<option>').val(value).text(key));
      });
      $('#household-investigator').trigger('liszt:updated');
    });
  });

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

});
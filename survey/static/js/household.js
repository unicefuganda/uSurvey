;

jQuery(function($){
  jQuery.validator.addMethod("validate_number_of_females", function(value, element) {
    var aged_between_15_19_years = parseInt($("#household-women-aged_between_15_19_years").val()),
        aged_between_20_49_years = parseInt($("#household-women-aged_between_20_49_years").val()),
        number_of_females = value;
    return (number_of_females >= aged_between_20_49_years + aged_between_15_19_years);
  }, "Please enter a value that is greater or equal to the total number of women above 15 years age.");

  $('#create-household-form').validate({
      ignore: ':hidden:not(select)',
      rules: {
        'age': 'required',
        'surname':'required',
        'first_name':'required',
        'occupation':'required',
        "number_of_females": "validate_number_of_females"
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

  function toggle_related_fields(field, related_field) {
    field.change(function(){
      if ($(this).val() == 'True'){
        related_field.removeAttr('disabled');
      }else{
        related_field.attr('disabled', 'disabled');
      };
    });
  }

  toggle_related_fields($('input[name=has_children_below_5]'), $('.children-below-5-field'));
  toggle_related_fields($('input[name=has_women]'), $('.women-field'));
  toggle_related_fields($('input[name=has_children]'), $('.children-field'));

  $('input[name=has_children]').change(function(){
    $('.has_children_below_5[value=' + $(this).val() + ']').prop('checked', true);
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
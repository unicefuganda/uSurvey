;

jQuery(function($){
  $(".chzn-select").chosen();
  $("#bulk-sms-locations").multiSelect();
});

function populate_investigator_list(location_id){
  $.getJSON('/households/investigators', {location: location_id}, function(data) {
      $.each(data, function(key, value) {
           $("#household-investigator")
                .append($('<option>')
                .val(value)
                .text(key));
      });

  $("#household-investigator").trigger("liszt:updated");
  });
};

function set_householdHead_occupation_values(){
    var select_value = $('select[name=occupation]').val();
    var input_value = $('input[name=occupation]').val();
    $('#extra-occupation-field').val(select_value + input_value);
};

$(function(){

  jQuery.validator.addMethod("validate_number_of_females", function(value, element) {
        var aged_between_15_19_years = parseInt($("#household-women-aged_between_15_19_years").val());
        var aged_between_20_49_years = parseInt($("#household-women-aged_between_20_49_years").val());
        var number_of_females = value;
        return (number_of_females >= aged_between_20_49_years + aged_between_15_19_years)
      }, "Please enter a value that is greater or equal to the total number of women above 15 years age.");

  $('#create-household-form').validate({
      ignore: ":hidden:not(select)",
      rules: {
        "age": "required",
        "surname":"required",
        "first_name":"required",
        "occupation":"required",
        "number_of_females": "validate_number_of_females"
      },
      messages: {
        "age":{ number: "Please enter a valid number. No space or special charcters."},
      },
      errorPlacement: function(error, element) {
        if ($(element).is(':hidden')) {
          error.insertAfter(element.next());
        } else {
          error.insertAfter(element);
        };
       },
      submitHandler: function(form){
         var button = $(form).find('button'),
             value = button.val();
         button.attr('disabled', true);
         set_householdHead_occupation_values();
         form.submit();
       }
  });

  $("input.small-positive-number").each(function(){
      $(this).rules('add', {required:true, min:0, max:10});
  });

  $("#household-number_of_males").change(function(){update_total_family_size();});
  $("#household-number_of_females").change(function(){update_total_family_size();});
  $.each( $("[id*=months]"), function(){
      $(this).change(function(){update_total_below_5_children();});
  });

  $("#household-women-has_women_1").change(function(){
          disable_selected("[id*=women]");
  });

  $("#household-children-has_children_1").change(function(){
            disable_selected("[id*=children]");
            $("#household-children-has_children_below_5_1").prop('checked', true);
    });

  $("#household-children-has_children_below_5_1").change(function(){
            disable_selected("[id*=children][id*=months]");
    });

  $("#household-women-has_women_0").change(function(){
      enable_selected("[id*=women]");
  });

  $("#household-children-has_children_0").change(function(){
          enable_selected("[id*=children]");
          $("#household-children-has_children_below_5_0").prop('checked', true);
  });

  $("#household-children-has_children_below_5_0").change(function(){
     if(!$("#household-children-has_children_1").is(':checked')){
          enable_selected("[id*=children][id*=months]");
     }
  });

  append_extra_input_field($('#household-occupation'));
  $('#household-occupation').change(function(){
      occupation = $(this);
      if(occupation.val() !=occupation.children().last().val()){
          $('#extra-occupation-field').remove();
          return true;
      };
      append_extra_input_field(occupation);
  });

  chosen_automatic_update("#household-extra_resident_since_year", "#household-resident_since_year");
  chosen_automatic_update("#household-extra_resident_since_month", "#household-resident_since_month");

  $('input[name=location]').on('fetch-investigator', function(){
      populate_investigator_list($(this).val());
  });

});

function update_total_family_size(){
    var males = parseInt($("#household-number_of_males").val());
    var females = parseInt($("#household-number_of_females").val());
    $("#household-size").val(males+females);
};

function update_total_below_5_children(){
    var total =0;
    $.each( $("[id*=_months]"), function(){
        total = total + parseInt($(this).val());
    });
    $("#household-children-total_below_5").val(total);
};

function append_extra_input_field(id){
  if(id.val()==id.children().last().val()){
      id.after("&nbsp; &nbsp;<input name='occupation' max_length=50 id='extra-occupation-field' Placeholder='Specify' type='text'/>");
      $("#extra-occupation-field").rules('add', {required:true});
  };
};

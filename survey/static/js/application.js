;

$(".chzn-select").chosen();

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

function populate_location_chosen(location_type, parent_id){
  $.getJSON('/investigators/locations', {parent: parent_id}, function(data) {
      $.each(data, function(key, value) {
           location_type
                .append($('<option>')
                .val(value)
                .text(key));
      });

  location_type.trigger("liszt:updated");
  });
};

function notify(location_type){
 var reset_option_text = '';
  if(location_type.attr('data-placeholder')=='All'){
    reset_option_text = 'All';
  }
  location_type
      .find('option')
      .remove()
      .end()
      .append('<option value="">'+ reset_option_text +'</option>');

  location_type.trigger("liszt:updated");
};

function notify_all(location_array){
    var i;
    for (i = 0; i < location_array.length; ++i) {
        notify($(location_array[i]));
    }
};

function update_get_investigator_list_link(id){
  filter_id = ""
  if (id){
    filter_id = "filter/"+ id +"/"
  }
  $("#a-investigator-list").attr("href", "/investigators/"+ filter_id);
};

function update_location_list(location_type, location_children, location_parent){
  $(location_type).chosen().change( function(){
       var location_value = $(location_type).val();
       if (location_value && location_children){
         populate_location_chosen($(location_children[0]), location_value);
         update_get_investigator_list_link(location_value)
        } else{
          update_get_investigator_list_link($(location_parent).val())
        }
        notify_all(location_children);
        if (location_children.length==0){
            $("#investigator-location").val(location_value);
            update_get_investigator_list_link(location_value);
            notify($("#household-investigator"));
            populate_investigator_list(location_value);
        }

     });
};

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

function set_householdHead_occupation_values(){
    var select_value = $('select[name=occupation]').val();
    var input_value = $('input[name=occupation]').val();
    $('#extra-occupation-field').val(select_value + input_value);
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
        "surname":"required",
        "first_name":"required",
        "occupation":"required",
        // "haha":{ min:0, max:10},
      },
      messages: {
        "age":{ number: "Please enter a valid number. No space or special charcters."},
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
         set_householdHead_occupation_values();
         form.submit();
       }
  });

  $("input.small-positive-number").each(function(){
      $(this).rules('add', {required:true, min:0, max:10});
  });

  $("#investigator-confirm_mobile_number").on('paste', function(e) {
    e.preventDefault();
  });

  var data_location = $("select[data-location=true]");
  data_location.each(function(index){
      update_location_list(this, data_location.slice(index+1), data_location.get(Math.min(index-1)));
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
      if($(this).val() !="Others: "){
          $('#extra-occupation-field').remove();
          return true;
      };

      append_extra_input_field($(this));
  });

  chosen_automatic_update("#household-extra_resident_since_year", "#household-resident_since_year");
  chosen_automatic_update("#household-extra_resident_since_month", "#household-resident_since_month");

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

function append_extra_input_field(id){
  if(id.val()=="Others: "){
      id.after("&nbsp; &nbsp;<input name='occupation' max_length=50 id='extra-occupation-field' Placeholder='Specify' type='text'/>");
      $("#extra-occupation-field").rules('add', {required:true});
  };
};

function chosen_automatic_update(given_id, hidden_id){
    $(given_id).trigger("liszt:updated").chosen().change(function(){
        $(hidden_id).val($(this).val());

    });
};
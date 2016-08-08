$(function(){

  jQuery.validator.addMethod("leading_zero_if_number_is_10_digits", function(value, element) {
      return ((value.length !=10) || (value[0]==0) )
    }, "The first digit should be 0 if you enter 10 digits.");

  jQuery.validator.addMethod("no_leading_zero_if_number_is_9_digits", function(value, element) {
      return ( (value.length !=9) || (value[0] !=0))
    }, "No leading zero. Please follow format: 771234567.");

  jQuery.validator.addMethod("validate_password", function(value, element) {
        return ($("#id_password1").val()==value)
      }, "Password not matched.");

  jQuery.validator.addMethod("validate_edit_password", function(value, element) {
        return ($("#id_password").val()==value)
      }, "Password not matched.");

  jQuery.validator.addMethod( "regex", function(value, element, regexp) {
                  var re = new RegExp(regexp);
                  return re.test(value);
              },"username may contain only letters characters."
      );

  $('#edit-user-form').validate({
      ignore: ":hidden:not(select)",
      rules: {
        "mobile_number": {
          required: true,
          minlength: 9,
          no_leading_zero_if_number_is_9_digits: true,
          leading_zero_if_number_is_10_digits: true
        },
        "email":{required:true},
        "confirm_password":{validate_edit_password: true},
      },
      messages: {
        "mobile_number": {
          number: "Please enter a valid number. No space or special charcters.",
          minlength:jQuery.format("Too few digits. Please enter {0} digits."),
        }
      },
      errorPlacement: function(error, element) {
        if ($(element).is(':hidden')) {
          error.insertAfter(element.next());
        } else {
          error.insertAfter(element);
        }
       },
      submitHandler: function(form){
         var button = $(form).find('button'),
             value = button.val();
         button.attr('disabled', true);
         form.submit();
       }
  });


  $('#create-user-form').validate({
      ignore: ":hidden:not(select)",
      rules: {
        "mobile_number": {
          required: true,
          minlength: 9,
          no_leading_zero_if_number_is_9_digits: true,
          leading_zero_if_number_is_10_digits: true,
          remote: '/users/',
        },
        "username":{required:true,
                    regex:'^[a-zA-Z]+$',
                    remote:'/users/'},
        "email":{required:true,
                    remote:'/users/'},
        "password1":{required: true},
        "password2":{validate_password: true, required: true},
        "password":{required: true},
        "confirm_password":{validate_edit_password: true, required: true},
        "groups":"required",
      },
      messages: {
        "mobile_number": {
          number: "Please enter a valid number. No space or special charcters.",
          minlength:jQuery.format("Too few digits. Please enter {0} digits."),
          remote: jQuery.format("{0} is already associated with a different user.")
        },
        "username": {
          remote: jQuery.format("{0} is no longer available.")
        },
        "email": {
          remote: jQuery.format("{0} is already associated with a different user.")
        },
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
         form.submit();
       }
  });

  $("input.small-positive-number").each(function(){
      $(this).rules('add', {required:true, min:0, max:10});
  });

  $("#investigator-confirm_mobile_number").on('paste', function(e) {
    e.preventDefault();
  });

  $('input[name=location]').on('change', function(){
      update_get_investigator_list_link($(this).val());
  });

});
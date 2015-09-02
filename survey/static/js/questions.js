$(function(){

	$.validator.addMethod("indetifier_is_available", identify_is_available, "Name already used for this batch");
	$.validator.addMethod("depends", function(val){
		if($('#validation_test').val() && !$('#validation_arg').val())
			return false;
		else
			return true;
	}, "No validation parameter");
	$.validator.addMethod("condition_is_available", function(val){
		var condition = get_condition($('#validation_test').val(), [$('#validation_arg').val(), ]);
		return condition_is_available(LAST_SELECTED_NODE, condition);
	}, "Condition already assigned");
	$('#question_form').validate({
    	  submitHandler: function(form) { 
    		  var new_question = {
    			identifier: form.identifier.value.trim(),
    			text: form.text.value.trim(),
    			answer_type: form.answer_type.value.trim(),
    			validation_test : form.validation_test.value.trim(), 
    			validation_arg : [form.validation_arg.value.trim(), ],
    			edit : $('#question_form').attr('edit'),
    		  }
    		  handle_node(new_question);  
    		  return false;
   		  },
      rules: {
        'text' : { required : true },
        'answer_type' : {required : true },
        'identifier': {required: true, 'indetifier_is_available' : true },
        'validation_test' : { required : false , 'condition_is_available' : true },
        'validation_arg' : {required : false, 'depends': true, 'condition_is_available' : true },
        }
      });

    var text_area = $('.question-form textarea'),
        counter = $('#text-counter'),
        maxlength = parseInt(text_area.attr('maxlength')),
        current_length = 0,
        counter_text = "/" + maxlength;

    text_area.on('keyup', function(){
        current_length = $(this).val().length;
        if (current_length > maxlength) return false;
        counter.html(current_length + counter_text);
    });

      $('.question-form').validate({
      rules: {
        'text':'required',
        'identifier':'required',
        'group':'required',
        'answer_type':'required'
      }
      });
     

           
});




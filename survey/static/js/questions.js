$(function(){
	$.validator.addMethod("indetifier_is_available", identify_is_available, "Name already used for this batch");
	$.validator.addMethod("depends", function(val){
		if($('#validation_test').val() && !$('#validation_arg').val())
			return false;
		else
			return true;
	}, "No validation parameter");
	$('#question_form').validate({
    	  submitHandler: function(form) { 
    		  var new_question = {
    			identifier: form.identifier.value.trim(),
    			text: form.text.value.trim(),
    			answer_type: form.answer_type.value.trim(),
    			edit : $('#question_form').attr('edit'),
    		  }
    		  handle_node(new_question);
   		  
    		  
    	  },
      rules: {
        'text' : { required : true },
        'answer_type' : {required : true },
        'identifier': {required: true, 'indetifier_is_available' : true }
        }
      });
     
     $('#question_flow_form').validate({
   	  submitHandler: function(form) { 
   		  var new_condition = {
   			validation_test : form.validation_test.value.trim(),
   			validation_arg: [form.validation_arg.value.trim(), ]
   		  }
   		  handle_edge(new_condition)
   		  	
   	  },
     rules: {
       'validation_test' : { required : false },
       'validation_arg' : {required : false, 'depends': true },
       }
     });

     $('#validation_test').change(function(evt){
    	 if($('#validation_test').val())
     		$('#validation_arg').show();
     	else
     		$('#validation_arg').hide(); 
     });
     
     $('#node_actions .add').click(function(evt) {
    	 $('#question_form').show();	
		 $('#question_flow_form').hide();
		 $('#batch_questions').hide();
    	 });
     $('#cancel_question_form, #cancel_question_flow_form').click(function(evt) {
    	 $('#question_form')[0].reset();
    	 $('#question_flow_form')[0].reset();
    	 $('#question_form, #question_flow_form').hide();
    	 $('#batch_questions').show();
    	 $('#p_question, #n_question').remove();
    	 $('#question_form').removeAttr('edit');
//    	 $('#create_question').show();
	 });
     $('#node_actions .edit').click(function(evt) {
    	 $('#batch_questions').hide();
    	 node = cy.$('node:selected[parent]')[0];
    	 $('#question_form #question').val(node.data('text'));
    	 $('#question_form #identifier').val(node.data('identifier'));
    	 $('#question_form #answer_type').val(node.data('answer_type'));
    	 $('#question_form').attr('edit', 'true');
    	 $('#question_form').show();
    	 });
     $('#edit_edge').click(function(evt) {
    	 edges = cy.$('edge:selected');
    	 if(edges.length > 0)
	    	{
	    		 $('#question_form').hide();	
	    		 build_edge_form(edges[0]);
	    		 $('#question_flow_form').show();
	    		 
	    	}
    	 $('#validation_arg').hide();
    	 $('#batch_questions').hide();
    	 });
     $('#node_actions .remove').click(function(evt) {
    	 remove_selected();
    	 });
     $("#lib_questions tr.ms-selectable").click(function(evt){
    	 
    	 var identifier = $( this ).children("td.question_identifier").text();
    	 if(identify_is_available(identifier))
    	{
    	 var new_question = {
					identifier: identifier,
					text: $( this ).children("td.question_text").text(),
					answer_type: $( this ).children("td.answer_type").text(),
				  }
		    	  handle_node(new_question);
    	}
    	else flash_message('identifier is already in use');
    	 
     });

	 
     
});




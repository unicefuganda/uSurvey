{% load template_tags %}
LAST_SELECTED = undefined;
TAPPED_BEFORE = null;
cy.on('select', 'node[parent]', function(evt) { //show node actions when node is selected
	var source = evt.cyTarget;
	if(source !== LAST_SELECTED && LAST_SELECTED !== undefined)
		LAST_SELECTED.unselect();
	LAST_SELECTED = source;
	var source_id = source.data('id');
	$('#canvas_actions').show(); 
	var node_edges = source.neighborhood('edge[target="'+source_id+'"]'); //root nodes are never edge target
	if(node_edges.length == 0)
	{
		$('#node_actions .remove').hide(); //you cannot remove the root node only edit
	}
	else
	 {
		 $('#node_actions .remove').show();
	 }
	 $('#node_actions').show(); 
	 $('#edge_actions').hide();
	});

cy.on('unselect', 'node[parent]', function(evt) { 
	$('#node_actions').hide();
	});

cy.on('select', 'edge', function(evt) { //edge actions when node is selected
	$('#canvas_actions').show(); 
	 $('#edge_actions').show(); 
	 $('#node_actions').hide();
	});

cy.on('unselect', 'edge', function(evt) { 
	$('#edge_actions').hide();
	});

cy.on('tap', function(event){
	var all_nodes = cy.$('node');
	
//	var nodes = cy.$('node:selected[parent]');
	//alert('all nodes!='+ all_nodes.length + ' my nodes '+ nodes.length);
	if(all_nodes.length > 0 && LAST_SELECTED === undefined)
		return;
	var evtTarget = event.cyTarget;
	  if( evtTarget === cy )
	  {
		  
		  console.log('tap on background');
	      if(all_nodes.length == 0)
	      {
	    	  first_question({text: '', identifier: '', answer_type: ''});
	      }
	      else
	    	  {
	    	  		$('#p_question').remove();
	    	     	LAST_SELECTED.select();
	    	     	insert_previous_question(LAST_SELECTED.data());
	    	     	enable_question_flow(LAST_SELECTED.data());
	    	     	build_new_question(LAST_SELECTED.data());
	    	  }
	      $('#canvas_actions').hide(); 
	      $('.lib_questions').show(); 
	  }

	});

$("#lib_questions tr.ms-selectable").click(function(evt)
{
	var all_nodes = cy.$('node');
	if(all_nodes.length > 0 && LAST_SELECTED === undefined)
		return flash_message('First select the node to connect to');
	 var identifier = $( this ).children("td.question_identifier").text();
	 if(identify_is_available(identifier))
	{
		 var new_question = {
					identifier: identifier,
					text: $( this ).children("td.question_text").text(),
					answer_type: $( this ).children("td.answer_type").text(),
				  }
		 if(all_nodes.length == 0)
	     {
	   	  first_question(new_question);
	     }
	     else build_question_from_lib(LAST_SELECTED.data(), new_question);
	}
	else flash_message('identifier is already in use');
});

$('#question_subm_form').submit(function(evt){
	graph = []
	var elems = cy.elements('node[parent], edge');
	//post only relevant data
	for(var i=0; i < elems.length; i++)
	{
		graph.push(elems[i].data());
	}
	$('#questions_data').val(JSON.stringify(graph));
	$('#submission_form').submit();
	flash_message($('#questions_data').val());
 });

$('#node_actions .remove').click(function(evt) {
	 elems = cy.$('node:selected[parent]');
	 source = elems[0];
	 var source_id = source.data('id');
	var node_edges = source.neighborhood('edge[target="'+source_id+'"]'); //root nodes are never edge target
	if(node_edges == 0)
	{
		return;  //should not be able to remove root node
	}
	 cy.batch(function(){
		    parent_nodes = elems.parent();
		    elems.remove();
		    parent_nodes.remove();
	    });
	 $(this).hide();
});


// form events
$('#validation_test').change(function(evt){
	 if($('#validation_test').val())
		$('#validation_arg').show();
	else
		$('#validation_arg').hide(); 
});

//$('#button').click(function(evt){
//	alert('hey man');
//})

$('#cancel_question_form').click(function(evt) {
	restore_canvas();
});

$('#node_actions .edit').click(function(evt) {
	 $('#batch_questions').hide();
	 $('#quest_flow_form_cont').hide();
	 node = cy.$('node:selected[parent]')[0];
	 $('#question_form #question').val(node.data('text'));
	 $('#question_form #identifier').val(node.data('identifier'));
	 $('#question_form #answer_type').val(node.data('answer_type'));
	 $('#question_form').attr('edit', 'true');
	 $('#question_form').show();
     $('#side_bar').show();
     $('#filz').show();
	 });

$('#edit_edge').click(function(evt) {
	$('#canvas_actions').hide(); 
	$('.lib_questions').hide(); 
	start_edge_edit();
});

$('#remove_edge').click(function(evt) {
	var edges = cy.$('edge:selected');
	if(edges.length > 0){
		edges[0].remove();
	}
});

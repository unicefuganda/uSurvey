{% load template_tags %}
$(function(){ // on dom ready
layout_opts = {
	    name: 'dagre',
	    padding: 5
	  };
cy = cytoscape({
  container: document.getElementById('batch_questions'),
  minZoom: 0.5,
  zoom: 0,
////  pan: { x: 0, y: 0 },
//  userPanningEnabled: true,
  boxSelectionEnabled: true,
  selectionType: 'single',
  maxZoom: 2,
  position: {x: 0, y: 0},
  style: [

    {
      selector: "node",
      css: {
        'shape': 'rectangle',
        'text-wrap': 'wrap',
        'text-valign': 'center',
        'text-halign': 'center',
        'height': '80px',
        'width' : '150px',
        'text-max-width': '100px',
        'font-size' : '10px',
        'padding-top': '10px',
        'padding-left': '10px',
        'padding-bottom': '10px',
        'padding-right': '10px',
        'background-color' : 'LightBlue',
      }
    },
    {
        selector: '$node[^parent]',
        css: {
      	  'content': 'data(id)',
      	  'text-valign': 'top',
          'height': '300px',
          'width' : '300px',        
        }
      },  
      {
          selector: '#add1, #edit1',
          css: {
        	  'content': 'data(id)',
        	  'width' : '30px',
        	  'height': '20px',
        	 'text-valign': 'center'
          }
        }, 
      {
          selector: '$node[parent]',
          css: {
        	 'content': 'data(text)',
          }
        },  
      {
          selector: '$node[fresh]',
          css: {
        	  'content': '',
        	  'height': '100px',
              'width' : '100px',
          }
      },  
      {
          selector: '$node[fresh][id="fresh_init"]',
          css: {
        	  'content': 'Click to start',
          }
      },
    {
      selector: 'edge',
      css: {
        'target-arrow-shape': 'triangle',
        'content' : 'data(condition)',
        'font-size': '8px',
      }
    },
    {
      selector: ':selected',
      css: {
        'background-color': 'tan',
        'line-color': 'black',
        'target-arrow-color': '#000080',
        'source-arrow-color': '#000080'
      }
    }
    
  ],
  
  elements: {
      nodes: [
              {% if batch_question_tree %}              
	          		{% for q_node in batch_question_tree %}
	          		    { data: { id: '{{q_node.identifier}}', } },
	               	    { data: {id: 'q_{{q_node.identifier}}' , identifier: '{{q_node.identifier}}', parent: '{{q_node.identifier}}', text: '{{ q_node.text }}' ,  key: '{{q_node.pk}}' , level: '{{ q_node.get_level }}',   answer_type:'{{q_node.answer_type}}'},},
	              {% endfor %}
	          {% else %}
	            { data: { id: 'fresh_cont', fresh:true}, locked: true, position: {x: -60, y: -60} },
         	    { data: {id: 'fresh_init' , parent: 'fresh_cont', text: 'Click to begin' ,  fresh: true},   },
		      {% endif %}
	          
            ],
            edges: [
  	           {% if batch_question_tree %}              
	          		{% for q_node in batch_question_tree %}
	          			{% for flow in q_node.flows.all %}
	          	        	{ data: { id: "{{q_node.identifier}}_{{flow.next_question.identifier}}", source: "q_{{q_node.identifier}}", target: "q_{{flow.next_question.identifier}}", condition: "{{ flow | show_condition }}", }, },
	          	        {% endfor %}
	               	{% endfor %}
		      {% endif %}
              
            ]
  },
  
  layout: layout_opts,
});
cy.on('select', 'node[parent]', function(evt) { //show node actions when node is selected
	nodes = cy.$('node:selected[parent]');
	if(nodes.length > 0 && nodes.data('level') == 0)
	{
		 $('#node_actions .remove').hide();
	}
	 else{
		 $('#node_actions .remove').show();
	 }
	$('#options').show(); 
	 $('#node_actions').show(); 
	 $('#edge_actions').hide();
	});

cy.on('unselect', 'node[parent]', function(evt) { 
	$('#node_actions').hide();
	$('#options').hide();
	});

cy.on('select', 'edge', function(evt) { //edge actions when node is selected
	 $('#edge_actions').show(); 
	 $('#node_actions').hide();
	});

cy.on('unselect', 'edge', function(evt) { 
	$('#edge_actions').hide();
	});
cy.on('select', 'node[fresh]', function() {
	$('#question_form').show();
	$('#node_actions, #edge_actions, #batch_questions').hide();
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

addStarterQuestion = function(new_data){
	var dat_id = 'q_'+new_data.identifier;
	var container_id = new_data.identifier;
	var new_level = 0;
	var elems = cy.add([
	                   { group: "nodes", data: { id: container_id }, },
	                   { group: "nodes", data: { id: dat_id, parent: container_id, level: new_level, identifier: new_data.identifier, text: new_data.text,  answer_type: new_data.answer_type}, },
	                 ]);
	elems[1].select();
	cy.$('node[fresh]').remove();
	$("#question_form .hide").removeClass('hide');
	$('#submit_action').show();
	return elems;
}

addFollowUp = function(pres_question_data, new_data){
	var dat_id = 'q_'+new_data.identifier;
	var container_id = new_data.identifier;
	var connection_id = pres_question_data.identifier + '_' + new_data.identifier;
	if(new_data.level === undefined)
	    new_level = pres_question_data.level + 1;
	
	var elems = cy.add([
	                   { group: "nodes", data: { id: container_id },},
	                   { group: "nodes",  data: { id: dat_id, parent: container_id, level: new_level, identifier: new_data.identifier, text: new_data.text, answer_type: new_data.answer_type}},
	                   { group: "edges", data: { id: connection_id, source: pres_question_data.id, 
	                	   target: dat_id, condition: new_data.condition_string, validation_test: '', 
	                	   validation_arg: [], } }
	                 ]);
	cy.elements().unselect();
	elems[2].select();
	return elems;
}

edit_question = function(selected, edit_data)
{
	if(selected.data('identifier') == edit_data.identifier)
	{
		selected.data('text', edit_data.text);
		selected.data('answer_type', edit_data.answer_type);
		return;
	}
	/* create new node with edit data and delete the old one. Attach selected node edges to new node */
	var dat_id = 'q_'+edit_data.identifier;
	var container_id = edit_data.identifier;
	var level = selected.data('level');
	var elems = cy.add([
	                   { group: "nodes", data: { id: container_id },},
	                   { group: "nodes",  data: { id: dat_id, parent: container_id, level: level, identifier: edit_data.identifier, text: edit_data.text, answer_type: edit_data.answer_type}},
	                 ]);
	cy.elements().unselect();
	elems[1].select();
	var node_edges = selected.neighborhood('edge');
	for(var i=0; i< node_edges.length; i++)
	{
		var edge = node_edges[i];
		var source = edge.data('source');
		var target = edge.data('target');
		switch(true)
		{
		case edge.data('source') == selected.data('id'):
			source = dat_id;
			break;
		case edge.data('target') == selected.data('id'):
			target = dat_id;
			break;
		}
		var connection_id = source + '_' + target;
		cy.add({ group: "edges", data: { id: connection_id, source: source, target: target, 
			condition: edge.data('condition'), validation_test: edge.data('validation_test'), 
			validation_arg: edge.data('validation_arg') } });
		edge.remove();
	}
	selected.remove();
	selected.parent().remove();

}

handle_node = function(elem_data){
	var selected_nodes = cy.$('node:selected');
	if(selected_nodes.length == 0)
		return flash_message('No node selected');
	selected = selected_nodes[0]
	switch(true)
	{
	case (cy.$('node[fresh]').length > 0):
		addStarterQuestion(elem_data);
		$('#cancel_question_form').click();
		break;
	case (elem_data.edit == 'true'):
		edit_question(selected, elem_data)
		$('#cancel_question_form').click();
		break;
	default:
		addFollowUp(selected.data(), elem_data);
		$('#edit_edge').click();
	}
	$('#submit_action').show();
	cy.layout({
	    name: 'dagre',
	    padding: 5
	  });
}

handle_edge = function(elem_data){
	var edges = cy.$('edge:selected');
	if(edges.length > 0)
	{
		edge = edges[0];
		var condition = '';
		if(elem_data.validation_test)
			condition = elem_data.validation_test + ' ( ' +  elem_data.validation_arg.join(", ") + ' )';
		if(condition_is_available(edge.source(), condition))
		{
			edge.data('condition', condition);
			edge.data('validation_test', elem_data.validation_test);
			edge.data('validation_arg', elem_data.validation_arg);
			cy.elements().unselect();
			edge.target().select();
			$('#cancel_question_form').click();
			return true;
		}
		else{
			flash_message('Flow already exist');
		}
		$('#submit_action').show();
	}
	else
		flash_message('No Connection selected');
	return false;
}


ques_validation_opts = {{ batch | quest_validation_opts }}
args_count = {{ batch | validation_args }}


build_edge_form = function(edge)
{
	
	answer_type = edge.source().data('answer_type');
	list(answer_type);
	if(answer_type == 'Date Answer')
    {
    	$( "#question_flow_form .validation_arg" ).datepicker();
    }
    else 
    {
    	$( "#question_flow_form .validation_arg" ).datepicker("destroy");
    }
	$('#quest_flow_form_cont').prepend('<h3 id="p_question">QUESTION:>'+ edge.source().data('text')+'</h3>');
	$('#quest_flow_form_cont').append('<h3 id="n_question">RESPOND WITH:>'+ edge.target().data('text')+'</h3>');
}

remove_selected = function() {
	 elems = cy.$('node:selected[parent]');
	 cy.batch(function(){
		    parent_nodes = elems.parent();
		    elems.remove();
		    parent_nodes.remove();
	    });
	 elems = cy.$('node:selected[parent]');
	 if(elems.length == 0)
		 $('#node_actions').show(); 
}

//function to populate child select box
function list(answer_type)
{
    $("#validation_test").html(""); //reset child options
    $("#validation_test").append('<option value="">------ is anything ------------</option>');
    array_list = ques_validation_opts[answer_type];
    $(array_list).each(function (i) { //populate child options
        $("#validation_test").append("<option value=\""+array_list[i].value+"\">"+array_list[i].display+"</option>");
    });
}

identify_is_available = function(identifier) {
	identifier = identifier.trim();
	var i = 0;
	var nodes = cy.$('node[parent]');
	selected_node = cy.$('node:selected[parent]')[0];
	var edit = $('#question_form').attr('edit') == 'true';
	var available = true;
	if((edit && selected_node.data('identifier') == identifier) == false)
		for (; i < nodes.length; i++) 
	    {   
			if((identifier) == nodes[i].data('identifier'))
	    	{
	    		available = false;
	    	}
	    }
	return available;
}

condition_is_available = function(source, condition) {
	var source_id = source.data('id');
	var node_edges = source.neighborhood('edge[source='+source_id+']');
	for (var i = 0; i < node_edges.length; i++) 
    {   
    	if(condition.trim() == node_edges[i].data('condition'))
    		return false;
    }
	return true;
}

flash_message = function(msg) {
	alert(msg);
}

}); // on dom ready
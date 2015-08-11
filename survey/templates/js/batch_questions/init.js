{% load template_tags %}
LAYOUT_OPTS = {
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
        'text-max-width': '150px',
        'font-size' : '10px',
        'padding': '1px',
        'border-style':'solid', 
  		'border-width':'1px', 
        'border-color':'#EFF1F1',
        'background-color' : 'white',

      }
    },
    {
        selector: '$node[^parent]',
        css: {
      	  'content': 'data(name)',
      	  'text-valign': 'top',     
		  'color' : 'green',
		  
        }
      },  
      {
          selector: '$node[parent]',
          css: {
        	 'content': 'data(text)',

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
        'background-color': '#EFF1F1',
        'line-color': '#EFF1F1',
        'target-arrow-color': '#FFFFFF',
        'source-arrow-color': '#FFFFFF'
      }
    }
    
  ],
  
  elements: {
      nodes: [
          		{% for q_node in batch_question_tree %}
          		    { data: { id: 'c_{{q_node.identifier}}', name: '{{q_node.identifier}}'} },
               	    { data: {id: '{{q_node.identifier}}', identifier: '{{q_node.identifier}}', parent: '{{q_node.identifier}}', text: '{{ q_node.text }}',  key: '{{q_node.pk}}' , answer_type:'{{q_node.answer_type}}'},},
              {% endfor %}
	          
            ],
            edges: [
  	           {% if batch_question_tree %}              
	          		{% for q_node in batch_question_tree %}
	          			{% for flow in q_node.flows.all %}
	          	        	{ data: { id: "{{q_node.identifier}}_{{flow.next_question.identifier}}", source: "{{q_node.identifier}}", target: "{{flow.next_question.identifier}}", condition: "{{ flow | show_condition }}", }, },
	          	        {% endfor %}
	               	{% endfor %}
		      {% endif %}
            ]
  },
  
  layout: LAYOUT_OPTS,
});


//the default values of each option are outlined below:
var defaults = {
  preview: false, // whether to show added edges preview before releasing selection
  handleSize: 10, // the size of the edge handle put on nodes
  handleColor: '#CDCDF1', // the colour of the handle and the line drawn from it
  handleLineType: 'ghost', // can be 'ghost' for real edge, 'straight' for a straight line, or 'draw' for a draw-as-you-go line
  handleLineWidth: 1, // width of handle line in pixels
  handleNodes: 'node[parent]', // selector/filter function for whether edges can be made from a given node
  hoverDelay: 150, // time spend over a target node before it is considered a target selection
  cxt: true, // whether cxt events trigger edgehandles (useful on touch)
  enabled: true, // whether to start the plugin in the enabled state
  toggleOffOnLeave: false, // whether an edge is cancelled by leaving a node (true), or whether you need to go over again to cancel (false; allows multiple edges in one pass)
  edgeType: function( sourceNode, targetNode ){
    // can return 'flat' for flat edges between nodes or 'node' for intermediate node between them
    // returning null/undefined means an edge can't be added between the two nodes
    return 'flat'; 
  },
  loopAllowed: function( node ){
    // for the specified node, return whether edges from itself to itself are allowed
    return false;
  },
  nodeLoopOffset: -50, // offset for edgeType: 'node' loops
  nodeParams: function( sourceNode, targetNode ){
    // for edges between the specified source and target
    // return element object to be passed to cy.add() for intermediary node
    return {};
  },
  edgeParams: function( sourceNode, targetNode, i ){
    // for edges between the specified source and target
    // return element object to be passed to cy.add() for edge
    // NB: i indicates edge index in case of edgeType: 'node'
    return {};
  },
  start: function( sourceNode ){
    // fired when edgehandles interaction starts (drag on handle)
  },
  complete: function( source, targetNodes, addedEntities ){
    // fired when edgehandles is done and entities are added
	var source_id = source.data('id');
	var node_edges = source.neighborhood('edge[target="'+targetNodes[0].data('id')+'"]');
	node_edges[0].select();
	start_edge_edit();
  },
  stop: function( sourceNode ){
    // fired when edgehandles interaction is stopped (either complete with added edges or incomplete)
    
  }
};

cy.edgehandles( defaults );

QUES_VALIDATION_OPTS = {{ batch | quest_validation_opts }} //QUES_VALIDATION_OPTS['answer_type'] = [validation_opts, val_opt2, ...]
ARGS_COUNT_MAP = {{ batch | validation_args }} //number of arguments for each arg count eg.  ARGS_COUNT_MAP['contains'] = 2, ARGS_COUNT_MAP['greater_than'] = 1 
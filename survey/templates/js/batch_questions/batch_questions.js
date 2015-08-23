{% load template_tags %}
$(function(){ // on dom ready
	{% include "js/batch_questions/init.js" with batch=batch batch_question_tree=batch_question_tree  %}
	{% include "js/batch_questions/events.js" with batch=batch batch_question_tree=batch_question_tree  %}
	{% include "js/batch_questions/functions.js" with batch=batch batch_question_tree=batch_question_tree  %}
}); // on dom ready
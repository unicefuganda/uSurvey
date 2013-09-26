;

function disable_field_based_on_value(field, value) {
    if (field.val() == value) {
        field.attr('disabled', 'disabled')
    }
}

function show_or_hide_attribute_fields(attribute_value){
    if(attribute_value == 'value'){
        $('#id_validate_with_question').hide();
        $('#id_value').show();
    }
    if(attribute_value == 'validate_with_question')
    {
        $('#id_validate_with_question').show();
        $('#id_value').hide();
    }
}
function show_or_hide_next_question(action_value) {
    show_next_question = ['SKIP_TO', 'ASK_SUBQUESTION'];

    if (show_next_question.indexOf(action_value) != -1) {
        $('#id_next_question').show()
    }
    else {
        $('#id_next_question').hide()
    }
}
jQuery(function($){
    var condition = $('#id_condition');
    var condition_value = 'EQUALS_OPTION';
    var attribute = $('#id_attribute');
    var attribute_value = 'option';
    var action_value = $('#id_action');

    disable_field_based_on_value(condition, condition_value);
    disable_field_based_on_value(attribute, attribute_value);
    show_or_hide_attribute_fields(attribute.val());
    show_or_hide_next_question(action_value.val());

    action_value.on('change', function(){
        show_or_hide_next_question($(this).val());
    });

    attribute.on('change', function(){
        show_or_hide_attribute_fields(attribute.val());
    });

});
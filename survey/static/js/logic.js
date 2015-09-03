;

function disable_field_based_on_value(field, value) {
    if (field.val() == value) {
        field.attr('disabled', 'disabled')
    }
}

function hide_between_value_fields() {
    var min_value_field = $('#id_min_value');
    var max_value_field = $('#id_max_value');

        min_value_field.hide();
        min_value_field.attr('disabled', 'disabled');
        max_value_field.hide();
        max_value_field.attr('disabled', 'disabled');
}

function show_between_value_fields(){
    var min_value_field = $('#id_min_value');
    var max_value_field = $('#id_max_value');
//    var validate_with_question_field = $('#id_validate_with_question');
    var value_field = $('#id_value');


        min_value_field.show();
        min_value_field.attr('disabled', false);
        max_value_field.show();
        max_value_field.attr('disabled', false);

  //      validate_with_question_field.hide();
   //     validate_with_question_field.attr('disabled', 'disabled');
        value_field.hide();
        value_field.attr('disabled', 'disabled');
}

function show_or_hide_attribute_fields(attribute_value){
   // var validate_with_question_field = $('#id_validate_with_question');
    var value_field = $('#id_value');

    hide_between_value_fields();

    if ($('#id_condition').val().toUpperCase() != 'BETWEEN'){
        hide_between_value_fields()
        if(attribute_value == 'value'){
     //       validate_with_question_field.hide();
       ///     validate_with_question_field.attr('disabled', 'disabled');
            value_field.show();
            value_field.attr('disabled', false);
        }

    }
    if ($('#id_condition').val().toUpperCase() == 'BETWEEN'){
        show_between_value_fields()
    }
}

function show_or_hide_next_question(action_value) {
    show_next_question = ['SKIP_TO', 'ASK_SUBQUESTION'];

    var next_question_field = $('#id_next_question');

    if (show_next_question.indexOf(action_value) != -1) {
        next_question_field.show();
        next_question_field.attr('disabled', false)
    }
    else {
        $('#add_subquestion').hide();
        next_question_field.hide();
        next_question_field.attr('disabled', 'disabled')
    }
}

function append_to_next_question_dropdown(data) {
    counter=0;
    $.each(data, function () {
        $('#id_next_question').append("<option value=" + data[counter]['id'] + ">" + data[counter]['text'] + "</option>");
        counter++;
    });
}

function append_to_drop_down_options(url)
{
    $.get( url, function( data ) {
        append_to_next_question_dropdown(data);
    });
    }

function replace_next_question_with_right_data(questions_url) {
    if(questions_url != ""){
    $('#id_next_question').find('option')
        .remove()
        .end()
    }
    append_to_drop_down_options(questions_url)
}

function append_attribute_option(key, value) {
    //$('#id_attribute').append("<option value=" + key + ">" + value + "</option>");
}

function clear_attribute_dropdown_and_append_right_option(condition_selected){
    condition_selected = condition_selected.toUpperCase()
//    var value_fields = ['GREATER_THAN', 'LESS_THAN', 'BETWEEN'];
////    var question_fields = ['GREATER_THAN_QUESTION', 'LESS_THAN_QUESTION'];
//    var value_and_question_conditions = ['EQUALS']
//    var value_key = 'value';
//    var value_string = 'Value';
//    var question_key = 'validate_with_question';
////    var question_string = 'Question';
//    $('#id_attribute').find('option')
//        .remove()
//        .end();
//
//    if(value_fields.indexOf(condition_selected) != -1){
//        append_attribute_option(value_key, value_string);
//    }
//
////    if(question_fields.indexOf(condition_selected) != -1){
////        append_attribute_option(question_key, question_string);
////    }
//
//    if(value_and_question_conditions.indexOf(condition_selected)!= -1){
//        append_attribute_option(value_key, value_string);
////        append_attribute_option(question_key, question_string)
//    }
    if(condition_selected == "BETWEEN"){
        $("#id_value").hide();
        show_between_value_fields();
    }
    else {
        $("#id_value").show();
        hide_between_value_fields();
    }


}

function fill_questions_or_subquestions_in_next_question_field(action_value){
    var show_questions = ['SKIP_TO'];
    var show_sub_questions = ['ASK_SUBQUESTION'];
    var question_id = $('#id_question').val();
    var batch_id = $('#id_batch').val()
    var questions_url = "";
    if(show_questions.indexOf(action_value) != -1)
    {
        questions_url = '/batches/'+ batch_id+'/questions/' + question_id +'/questions_json/'
        $('#add_subquestion').hide();
    }
    else if (show_sub_questions.indexOf(action_value) != -1)
    {
        questions_url = '/questions/' + question_id +'/sub_questions_json/'
        $('#add_subquestion').show();
    }
    replace_next_question_with_right_data(questions_url);
}

function isHTML(str) {
    var a = document.createElement('div');
    a.innerHTML = str;
    for (var c = a.childNodes, i = c.length; i--; ) {
        if (c[i].nodeType == 1) return true;
    }
    return false;
}

function clear_all_errors(){
    $('#id_value').next().text('');
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
    $('#add_subquestion').hide();

    condition.on('change', function(){
//        clear_attribute_dropdown_and_append_right_option(condition.val());
        show_or_hide_attribute_fields(attribute.val());
    });

    action_value.on('change', function(){
        show_or_hide_next_question($(this).val());
        fill_questions_or_subquestions_in_next_question_field(action_value.val());
    });

    attribute.on('change', function(){
        clear_all_errors();
        show_or_hide_attribute_fields(attribute.val());
    });

    var $add_question_form = $('#add-question-form');
    $add_question_form.validate({
      rules: {
        'text':'required',
        'identifier':'required',
        'group':'required',
        'answer_type':'required'
      },
      submitHandler: function(form){
        var $form = $(form),
            url = $form.attr("action"),
            data = $form.serialize();
        var post = $.post(url, data);

        post.done(function(data){
            if(data){
                $('#id_next_question').append("<option value=" + data['id'] + ">" + data['text'] + "</option>");
                $('#close_modal').click();
            } else{
                append_error_to_text(data);
            }
        });
      }
      });

    function subquestion_saved(data){
      return !isHTML(data);
    };

    function append_error_to_text(data){
        var text_error_field_on_page = $('#id_text').next(),
            text_error_ajax_result = $(data).find('#id_text').next().text();
        text_error_field_on_page.text('');
        if(text_error_ajax_result != ''){
            text_error_field_on_page.text(text_error_ajax_result);
            text_error_field_on_page.show();
        }
    };
});
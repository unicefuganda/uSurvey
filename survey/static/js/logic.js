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
    var value_field = $('#id_value');
    min_value_field.show();
    min_value_field.attr('disabled', false);
    max_value_field.show();
    max_value_field.attr('disabled', false);
    value_field.hide();
    value_field.attr('disabled', 'disabled');
}

function show_or_hide_attribute_fields(attribute_value){
    var value_field = $('#id_value');

    hide_between_value_fields();

    if ($('#id_condition').val() && $('#id_condition').val().toUpperCase() != 'BETWEEN'){
        hide_between_value_fields()
        if(attribute_value == 'value'){
            value_field.show();
            value_field.attr('disabled', false);
        }

    }
    if ($('#id_condition').val() && $('#id_condition').val().toUpperCase() == 'BETWEEN'){
        show_between_value_fields()
    }
}

function show_or_hide_next_question(action_value) {
    show_next_question = ['SKIP_TO', 'ASK_SUBQUESTION', 'BACK_TO'];
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
    $(' .chzn-select').trigger("liszt:updated");
}

var id_text_delim = ":    ";

function append_to_next_question_dropdown(data) {
    counter=0;
    $('#id_next_question').append('<option value="">Question-Code'+id_text_delim+'Text</option>');
    $.each(data, function () {
        $('#id_next_question').append('<option value="' + data[counter]['id'] + '">' + data[counter]['identifier'] + id_text_delim + data[counter]['text'] + "</option>");
        counter++;
    });
    change_to_select2($('#id_next_question'));
//     $(' .chzn-select').trigger("liszt:updated");
//     $('#id_next_question').select2({
//        templateResult: next_question_format,
//        templateSelection: next_question_select_format,
//        theme: "classic",
//    });
}

function change_to_select2(obj, delimiter, show_entire_selected) {
     if(!delimiter)
         delimiter = id_text_delim;
     show_entire_selected =  show_entire_selected === true ? true : false;
     obj.select2({
        templateResult: function(state) { return item_list_format(state, delimiter) },
        templateSelection: function(state) { return item_select_format(state, delimiter, show_entire_selected) },
        theme: "classic",
    });
}

function item_list_format(state, delimiter) {
    var key_terminus = state.text.indexOf(delimiter);
    //alert(JSON.stringify(state))
//    if(state.disabled === true)
//        return '';
    if(state.id){    // to do: handle this more elegantly
        var key = state.text.substring(0, key_terminus);
        var val = state.text.substring(key_terminus + 1);
    }
    else{
        var key = '<strong class="opt-header">'+state.text.substring(0, key_terminus)+'</strong>';
        var val = '<strong class="opt-header">'+state.text.substring(key_terminus + 1)+'</strong>';
    }
    return $('<div class="opt-item"><span class="opt-id" style="display: inline-block; padding-right: 2%; width: 40%; word-wrap:break-word;">' + key +
    '</span><span class="opt-text" style="display: inline-block; word-wrap:break-word;">'+ val + '</span></div>');
}

function item_select_format(state, delimiter, show_entire_selected) {
    if(state.id){
        var key_terminus = state.text.indexOf(delimiter);
        if(show_entire_selected)
            var content_to_show = state.text;
        else
            var content_to_show = state.text.substring(key_terminus + 1);
        var text = '<span style="color: #3875d7">' + content_to_show + '</span>';
    }
    else{
        var text =  '<strong>Choose Item</strong>';
     }

    return $('<div align="center">' + text + '</div>');
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
    $(' .chzn-select').trigger("liszt:updated");
}

function append_attribute_option(key, value) {
    //$('#id_attribute').append("<option value=" + key + ">" + value + "</option>");
}

function clear_attribute_dropdown_and_append_right_option(condition_selected){
    condition_selected = condition_selected.toUpperCase()
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
    var show_back_to_questions = ['BACK_TO'];
    var question_id = $('#id_question').val();
    var batch_id = $('#id_batch').val();
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
    else if(show_back_to_questions.indexOf(action_value) != -1)
    {
        questions_url = '/questions/' + question_id +'/prev_questions_json/'
        $('#add_subquestion').hide();
    }
    if(questions_url)
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
                 $('#id_next_question').append("<option value=" + data['id'] + ">" + data['identifier'] + id_text_delim + data['text'] + "</option>");
                $('#close_modal').click();
            } else{
                append_error_to_text(data);
            }
            $(' .chzn-select').trigger("liszt:updated");
        });
      }
      });
    fill_questions_or_subquestions_in_next_question_field(action_value.val());
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
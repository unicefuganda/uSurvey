;

function hide_field(field) {
        field.hide();
        field.attr('disabled', 'disabled');
}

function show_field(field) {
        field.show();
        field.attr('disabled', false);
}

function show_or_hide_based_on_denominator_type(denominator_type_value) {
    show_group = ['GROUP'];
    var group_field = $('#id_groups');
    var denominator_field = $('#id_denominator');
    var count_field = $('#id_count');
    var denominator_option_field = $('#id_denominator_options');

     if (show_group.indexOf(denominator_type_value) != -1) {
         show_field(group_field);
         hide_field(denominator_field);
         hide_field(count_field);
         hide_option_field_and_clear_field(denominator_option_field);
    }
    else {
         hide_field(group_field);
         show_field(denominator_field);
         show_or_hide_options_based_on_field_question_type(denominator_field, denominator_option_field);
         show_or_hide_options_based_on_field_question_type(count_field, denominator_option_field);
         show_field(count_field);
    }
}

function show_option_field_and_fill_field(option_field, options)
{
    var option_field_label = $("label[for='"+option_field.attr('id')+"']");

    option_field.find('option').remove().end();
    $.each(options, function(key, value){
        option_field.append("<option value=" + value['id'] + ">" + value['text'] + "</option>");
    });

    show_field(option_field);
    option_field_label.show();
    option_field_label.parent('.control-group').show();
}

function hide_option_field_and_clear_field(option_field)
{
    var option_field_label = $("label[for='"+option_field.attr('id')+"']");
    option_field.find('option').remove().end();
    hide_field(option_field);
    option_field_label.hide();
    option_field_label.parent('.control-group').hide()
}

function show_or_hide_options_based_on_field_question_type(question_field, options_field) {
    if (question_field.val() != undefined)
    {
        var url = '/questions/'+ question_field.val() +'/is_multichoice/';
        $.get( url, function( data ) {
            var is_multichoice = data[0].is_multichoice;
            var options = data[0].question_options;

            if (is_multichoice){
                show_option_field_and_fill_field(options_field, options)
            }else{
                hide_option_field_and_clear_field(options_field)
            }
        });
    }else{
        hide_option_field_and_clear_field(options_field)
    }
}

jQuery(function($){
    var denominator_type = $('#id_denominator_type');
    var denominator_type_value = denominator_type.val();
    var numerator_question_field = $('#id_numerator');
    var numerator_option_field = $('#id_numerator_options');
    var denominator_question_field = $('#id_denominator');
    var denominator_option_field = $('#id_denominator_options');
    var count_field = $('#id_count');

    show_or_hide_based_on_denominator_type(denominator_type_value);
    show_or_hide_options_based_on_field_question_type(numerator_question_field, numerator_option_field);
    show_or_hide_options_based_on_field_question_type(denominator_question_field, denominator_option_field);
    show_or_hide_options_based_on_field_question_type(count_field, denominator_option_field);

    denominator_type.on('change', function(){
        show_or_hide_based_on_denominator_type(denominator_type.val());
    });

    numerator_question_field.on('change', function(){
        show_or_hide_options_based_on_field_question_type(numerator_question_field, numerator_option_field);
    });

    denominator_question_field.on('change', function(){
        show_or_hide_options_based_on_field_question_type(denominator_question_field, denominator_option_field);
    });

    count_field.on('change', function(){
        show_or_hide_options_based_on_field_question_type(count_field, denominator_option_field);
    });
});
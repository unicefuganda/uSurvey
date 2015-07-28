$(function(){


    $('#ea-locations').on('change', function () {
    	reload_questions_lib();
    });

function reload_questions_lib()
{

	var group_selected = $('#id_groups').val();
    var module_selected = $('#id_modules').val();
    var answer_type_selected = $('#id_question_types').val();
    url = '/question_library/json_filter/';
    params = { question_types: answer_type_selected, groups : group_selected, modules: module_selected }
    $.getJSON(url, params, function (data) {
        $('.ms-selectable').hide()
        $.each(data, function () {
            $('#' + this.id + '-selectable').show();
        });
    });
}




});
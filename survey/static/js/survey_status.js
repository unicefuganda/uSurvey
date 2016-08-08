;
function get_survey_batches(val) {
    $.get('/surveys/' + val + '/survey_batches/', function (data) {
        $('#id_batch').find('option')
            .remove()
            .end();
        counter = 0;
        $('#id_batch').append('<option value="">----</option>');
        $.each(data, function () {
            $('#id_batch').append("<option value=" + data[counter]['id'] + ">" + data[counter]['name'] + "</option>");
            counter++;
        });
    });
}
jQuery(function($){
  $("#id_survey").on('change',function(){
        get_survey_batches($(this).val());
  });
});
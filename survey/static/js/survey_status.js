;
function get_survey_batches(val) {
    $.get('/surveys/' + val + '/survey_batches/', function (data) {
        $('#batch-list-select').find('option')
            .remove()
            .end();
        counter = 0;
        $.each(data, function () {
            $('#batch-list-select').append("<option value=" + data[counter]['id'] + ">" + data[counter]['name'] + "</option>");
            counter++;
        });
    });
}
jQuery(function($){
  $("#survey-list-select").on('change',function(){
      get_survey_batches($(this).val());
  });
});
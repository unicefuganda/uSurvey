;
function get_survey_batches(val) {
    $.get('/surveys/' + val + '/batches/', function (data) {
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
  get_survey_batches($("#survey-list-select").val());
  $("#survey-list-select").on('change',function(){
      get_survey_batches($(this).val());
  });
});
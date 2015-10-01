;
jQuery(function($){
    var batch = $("#id_batch");

    $("#id_filter_survey").on('change', updateBatchSelectField);
    $('#id_survey').on('change', updateBatchSelectField);

    function updateBatchSelectField () {
       batch.find('option').remove();
        batch.append($('<option />').val('').text('Select Batch'));
        populate_choices.call(this);
    }

    function get_url(survey_id){
        if (survey_id == 'All'){
            return '/batches/'
        }
        return '/surveys/'+ survey_id +'/survey_batches/';
    }

    function populate_choices() {
        var url = get_url($(this).val());
        $.getJSON(url, function (data) {
            $.each(data, function () {
                batch.append($('<option />').val(this.id).text(this.name));
            });
        });
    }
    if(batch.val().length == 0)
        $('#id_survey').trigger("change");

});
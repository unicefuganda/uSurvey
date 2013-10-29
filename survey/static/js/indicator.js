;
jQuery(function($){
    var $batch = $("#id_batch");
    $("#id_filter_survey").on('change', function(){
          $batch.find('option').remove();
          $batch.append($('<option />').val('All').text('All'));
         populate_choices.call(this)
    });

    $('#id_survey').on('change', function(){
        $batch.find('option').remove();
        populate_choices.call(this);
    });

    function get_url(survey_id){
        if (survey_id == 'All'){
            return '/batches/'
        }
        return '/surveys/'+ survey_id +'/batches/';
    }

    function populate_choices() {
        var url = get_url($(this).val());
        $.getJSON(url, function (data) {
            $.each(data, function () {
                $batch.append($('<option />').val(this.id).text(this.name));
            });
        });
    }

});
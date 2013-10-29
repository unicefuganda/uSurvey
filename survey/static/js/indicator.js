;
jQuery(function($){
    var $batch = $("#id_batch");
    $("#id_survey").on('change', function(){
          $batch.find('option').remove();
          option = get_first_option();
          $batch.append(option);
          var url = get_url($(this).val());
          $.getJSON(url, function(data){
               $.each(data, function(){
                   option = $('<option />').val(this.id).text(this.name);
                   $batch.append(option);
                });
          });
    });

    function get_first_option(){
        if (window.location.pathname.contains("new")){
            return '';
        }
        return $('<option />').val('All').text('All');
    }

    function get_url(survey_id){
        if (survey_id == 'All'){
            return '/batches/'
        }
        return '/surveys/'+ survey_id +'/batches/';
    }
});
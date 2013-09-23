;

function set_display(text, set){
    var all_elements = $('.ms-selectable').children().children();

    for(var counter=0; counter<all_elements.length; counter++)
    {
        element = all_elements[counter];

        if(set){
         if (text == element.childNodes[0].childNodes[0].nodeValue){
             element.style.display = ''
         }
        }
        else{
            element.style.display = 'none'
        }
    }
};


jQuery(function($){

    load_questions_for_batch_and_group();

  $('.switch').on('switch-change', function(e, data){
    var $el = $(data.el), form;
    if (data.value) {
      form = $el.parents('tr').find('form.open-for-location-form');
    }else{
      form = $el.parents('tr').find('form.close-for-location-form');
    }
    $.post(form.attr('action'), form.serializeArray(), function(){
      // do nothing
    });
  });

  var survey_id = $("#survey_id").val();
  $('#add-batch-form').validate({
      rules: {
        'name': {required:true, remote:'/surveys/'+ survey_id +'/batches/check_name/'},
        'description':'required'
      },
      messages: {
        "name": {
          remote: jQuery.format("Batch with the same name already exists.")
        }
      }

   });

  $('#assign_question_group').on('change', function(){
      load_questions_for_batch_and_group();
  });

});


function load_questions_for_batch_and_group(){
    var select_element = $('#assign_question_group'),
        batch_id = $("#batch_id").val(),
        url = '/batches/'+ batch_id +'/questions/groups/'+ select_element.val();
    $.getJSON(url, function(data){
        set_display('', false);
        $.each(data, function(){
            set_display(this.text, true);
        });
    });
}
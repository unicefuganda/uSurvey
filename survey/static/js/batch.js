;
jQuery(function($){
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

  $('#add-batch-form').validate({
      rules: {
        'name': 'required',
        'description':'required'
      }
   });

  $('#assign_question_group').on('change', function(){
      var select_element = $(this),
      url = '/questions/groups/'+ select_element.val();
      $.getJSON(url, function(data){
          $('#id_questions').html("");
          $.each(data, function(){
                  option = $('<option/>').val(this.id).text(this.text);
              $('#id_questions').append(option);
          });
          $('.multi-select').multiSelect('refresh');
    });
  });

});



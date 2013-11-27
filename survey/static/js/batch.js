;

jQuery(function($){
  if ($('#assign_question_group').val()){
        load_questions_for_filter();
    }

  $('.switch-open-close').on('switch-change', function(e, data){
      toggleStatus($(this), ['open-for-location-form', 'close-for-location-form'], data, true)
  });

  $('.switch-activate-non-response').on('switch-change', function(e, data){
        toggleStatus($(this), ['activate-non_response-for-location-form', 'deactivate-non_response-for-location-form'], data, false)
  });

  var survey_id = $("#survey_id").val(),
      $add_batch_form = $('#add-batch-form');

  $add_batch_form.validate({
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

  $('#edit-batch-form').validate({
      rules: {
        'name': 'required',
        'description':'required'
      }
   });


  $('#assign_question_group').on('change', function(){
      load_questions_for_filter();
  });
  $('#assign_module').on('change', function(){
      load_questions_for_filter();
  });

});



function load_questions_for_filter(){
    var group_selected = $('#assign_question_group').val();
    var module_selected = $('#assign_module').val(),
        batch_id = $("#batch_id").val(),
        url = '/batches/'+ batch_id +'/questions/groups/'+ group_selected + '/module/' + module_selected +'/';
    $.getJSON(url, function(data){
        $('.ms-selectable').children().children().hide();
        $.each(data, function(){
             $('#' + this.id + '-selectable').show();
        });
    });
}

function toggleStatus(element, forms_ids, data, switch_open_close){
    element.parent().find('.error').remove();
    var $el = $(data.el), form;
    if (data.value) {
      form = $el.parents('tr').find('form#'+forms_ids[0]);
    }else{
      form = $el.parents('tr').find('form#'+forms_ids[1]);
    }
    $.post(form.attr('action'), form.serializeArray(), function(data){
        if(data !='') {
             element.bootstrapSwitch('toggleState');
             element.bootstrapSwitch('setActive', false);
             element.after('<span><label class="error">' + data + '</label></span>');
        }
    });

}
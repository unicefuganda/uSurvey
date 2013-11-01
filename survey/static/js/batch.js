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
  if ($('#assign_question_group').val()){
        load_questions_for_batch_and_group();
    }
  $('.switch').on('switch-change', function(e, data){
    var current_switch = $(this);
    current_switch.parent().find('.error').remove();
    var $el = $(data.el), form;
    if (data.value) {
      form = $el.parents('tr').find('form.open-for-location-form');
    }else{
      form = $el.parents('tr').find('form.close-for-location-form');
    }
    $.post(form.attr('action'), form.serializeArray(), function(data){
        if(data !=''){
            current_switch.bootstrapSwitch('toggleState');
            current_switch.bootstrapSwitch('setActive', false);
            current_switch.after('<span><label class="error">' + data + '</label></span>');
        }
    });
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
      load_questions_for_batch_and_group();
  });
  $('#assign_module').on('change', function(){
      load_questions_for_batch_and_group();
  });

});


function load_questions_for_batch_and_group(){
    var group_selected = $('#assign_question_group').val();
    var module_selected = $('#assign_module').val(),
        batch_id = $("#batch_id").val(),
        url = '/batches/'+ batch_id +'/questions/groups/'+ group_selected + '/module/' + module_selected +'/';
    $.getJSON(url, function(data){
        set_display('', false);
        $.each(data, function(){
            representation = this.text + ": (" + this.answer_type.toUpperCase() + ")"
            set_display(representation , true);
        });
    });
}
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
          set_display('', false);
          $.each(data, function(){
              set_display(this.text, true);
          });
    });
  });

});



$(function(){
    var text_area = $('.question-form textarea'),
        counter = $('#text-counter'),
        maxlength = parseInt(text_area.attr('maxlength')),
        current_length = 0,
        counter_text = " of " + maxlength + " characters";

    text_area.on('keydown', function(){
        current_length = $(this).val().length;
        if (current_length > maxlength) return false;
        counter.html(current_length + counter_text);
        this.focus();
    });

      $('.question-form').validate({
      rules: {
        'text':'required',
        'identifier':'required',
        //'group':'required',
        'answer_type':'required'
      }
      });

           
});




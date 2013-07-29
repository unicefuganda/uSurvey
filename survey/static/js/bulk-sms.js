;
jQuery(function($){
  var textarea = $('#bulk-sms-form textarea'),
      counter = $('#sms-chars-left'),
      maxlength = parseInt(textarea.attr('maxlength')),
      current_length = 0,
      counter_text = "/" + maxlength;

  textarea.on('keyup', function(){
    current_length = $(this).val().length;
    if (current_length > maxlength) return false;
    counter.html(current_length + counter_text);
  });
});
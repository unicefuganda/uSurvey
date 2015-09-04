;

jQuery(function(){
  var transactionId = $("#transactionId"),
      transactionTime = $("#transactionTime"),
      response_true = $("#response-true"),
      response_false = $("#response-false"),
      timeout_true = $("#timeout-true"),
      timeout_false = $("#timeout-false"),
      server_response = $("#server-response"),
      user_response = $("#ussdRequestString"),
      simulator = $("#simulator-form"),
      timer = $("#timer"),
      delay = 0;

  function show_or_hide_timer(is_selected) {
    if (is_selected) {

        timer.show()
    }
    else {
        timer.text("03 min 00 sec");
        timer.removeClass('ended').data('countdown').update(+(new Date) + 180000).stop();
        timer.hide()
    }
  }

  function form_reset () {
    transactionId.val(Math.floor((Math.random()*100000)));
    response_true.removeAttr('checked');
    response_false.prop('checked', true);
    server_response.text('');
    user_response.val('');
  }

  function startTimer () {
    timer.countdown({
      render: function(data) {
        $(this.el).text(this.leadingZeros(data.min, 2) + " min " + this.leadingZeros(data.sec, 2) + " sec");
      },
      onEnd: function(){
        $(this.el).addClass('ended');
        form_reset();
      }
    });
    timer.removeClass('ended').data('countdown').update(+(new Date) + 180000).start();
  }

  form_reset();
  show_or_hide_timer(timeout_true.is(':checked'));

  timeout_true.on("change", function(){
      show_or_hide_timer(timeout_true.is(':checked'));
  });

  timeout_false.on("change", function(){
      show_or_hide_timer(!timeout_false.is(':checked'));
  });

  function ussd_submit () {
    $.get('/ussd', simulator.serializeArray(), function(data){
      if (timeout_true.is(':checked'))
        startTimer();
      var response = data.split("&action=")[0];
      response = response.split("responseString=")[1];
      server_response.text(response);
    }).fail(function(data){
      alert("There is an error!");
    }).always(function(){
      response_false.removeAttr('checked');
      response_true.prop('checked', true);
      user_response.blur().val('').focus();
      $('#form-control, #loader').toggleClass('hide');
    });
  }

  simulator.submit(function(){
    $('#form-control, #loader').toggleClass('hide');
    window.setTimeout(ussd_submit, delay * 1000);
    return false;
  });
});
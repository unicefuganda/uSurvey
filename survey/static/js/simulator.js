;

jQuery(function(){
  var timeout_true = $("#id_use_timeout_0"),
      timeout_false = $("#id_use_timeout_1"),
      timer = $("#id_use_timeout"),
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


  show_or_hide_timer(timeout_true.is(':checked'));

  timeout_true.on("change", function(){
      show_or_hide_timer(timeout_true.is(':checked'));
  });

  timeout_false.on("change", function(){
      show_or_hide_timer(!timeout_false.is(':checked'));
  });

});
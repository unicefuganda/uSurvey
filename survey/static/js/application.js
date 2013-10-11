;
$(function(){
    $(".chzn-select").chosen();
    $(".multi-select").multiSelect();
    $(".no-paste").on("paste", function(e){
      e.preventDefault();
    });
    $( ".datepicker" ).datepicker({
      changeMonth: true,
      changeYear: true,
      dateFormat:'yy-mm-dd',
      minDate: "-99Y",
      maxDate: "+1D",
      yearRange: "-99:+1"
    });

    $('.modal-body .form-actions a').removeAttr('href').attr('data-dismiss', 'modal');

    $('a[name=cancel_button]').on('click', function(){
        goBack();
    });
    function goBack() {
        window.location = document.referrer;
     }
});

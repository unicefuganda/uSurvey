;
$(function(){
    $(".chzn-select").chosen();
    $(".multi-select").multiSelect();
    $(".no-paste").on("paste", function(e){
      e.preventDefault();
    });
    
    $('.datepicker').datepicker({dateFormat:'yy-mm-dd'});
    $('.modal-body .form-actions a').removeAttr('href').attr('data-dismiss', 'modal');

    $('a[name=cancel_button]').on('click', function(){
        goBack();
    });
    function goBack() {
        window.location = document.referrer;
     }
});

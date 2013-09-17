;
$(function(){
  $(".chzn-select").chosen();
  $(".multi-select").multiSelect();
  $(".no-paste").on("paste", function(e){
    e.preventDefault();
  });
});

$(function(){
    $('.datepicker').datepicker({dateFormat:'yy-mm-dd'});
    $('.modal-body .form-actions a').removeAttr('href').attr('data-dismiss', 'modal');
});


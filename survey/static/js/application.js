;
$(function(){
  $(".chzn-select").chosen();
  $("#bulk-sms-locations").multiSelect();
  $(".no-paste").on("paste", function(e){
    e.preventDefault();
  });
});

$(function(){
    $('.datepicker').datepicker({dateFormat:'yy-mm-dd'});
});
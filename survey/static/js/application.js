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
});
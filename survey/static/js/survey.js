 ;

 function show_or_hide_sample_size() {
     var $sample_size = $('#id_sample_size');
     var $div_to_toggle = $sample_size.closest('div').parent('div');

     
     if($("input[name=has_sampling][value=True]").is(":checked")) {
         $div_to_toggle.show();
         show_or_hide_preferred_listing(true);
     }
     else {
         $div_to_toggle.hide();
         $sample_size.val(0);
         show_or_hide_preferred_listing(false);
     }
 }

 function show_or_hide_preferred_listing(show) {
      var $preferred_listing = $('#id_preferred_listing');
     var $div_to_toggle = $preferred_listing.closest('div').parent('div');
     if(show) {
         $div_to_toggle.show();
     }
     else {
         $div_to_toggle.hide();
         $preferred_listing.val("");
     }

 }

 jQuery(function($){
     show_or_hide_sample_size();
     $('input[name=has_sampling]').on('change', function(){
         show_or_hide_sample_size();
     });
 });

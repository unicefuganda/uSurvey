 ;

 function show_or_hide_sample_size() {
     var $sample_size = $('#id_sample_size');
     var $div_to_toggle = $sample_size.closest('div').parent('div');

     
     if($("input[name=has_sampling][value=True]").is(":checked")) {
         $div_to_toggle.show();
         show_or_hide_sampled_survey_field(true);
     }
     else {
         $div_to_toggle.hide();
         $sample_size.val(0);
         show_or_hide_sampled_survey_field(false);
     }
 }

 function show_or_hide_sampled_survey_field(show) {
     var $preferred_listing = $('#id_preferred_listing');
     var $listing_form = $('#id_listing_form');
     var $div_to_toggle = $preferred_listing.closest('div').parent('div');
     var $l_div_to_toggle = $listing_form.closest('div').parent('div');
     if(show) {
         $div_to_toggle.show();
         $l_div_to_toggle.show();
         $preferred_listing.removeAttr('disabled');
         $listing_form.removeAttr('disabled');
     }
     else {
         $div_to_toggle.hide();
         $preferred_listing.val("");
         $preferred_listing.attr('disabled', 'disabled');
         $l_div_to_toggle.hide();
         $listing_form.val("");
         $listing_form.attr('disabled', 'disabled');
     }

 }

 jQuery(function($){
     show_or_hide_sample_size();
     $('input[name=has_sampling]').on('change', function(){
         show_or_hide_sample_size();
     });
 });

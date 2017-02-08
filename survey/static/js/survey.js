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
     /*$("#id_listing_form").append($('<option value="val"/>').text('--Select Listing Form--'));
    $("#id_listing_form").val("val");*/
     var $div_to_toggle = $preferred_listing.closest('div').parent('div');
     var $l_div_to_toggle = $listing_form.closest('div').parent('div');
     if(show) {
         $div_to_toggle.show();
         $l_div_to_toggle.show();
         $preferred_listing.removeAttr('disabled');
         $listing_form.removeAttr('disabled');
         $('#id_random_sample_label-control-group').show();
     }
     else {
         $div_to_toggle.hide();
         $preferred_listing.val("");
         $preferred_listing.attr('disabled', 'disabled');
         $l_div_to_toggle.hide();
         $listing_form.val("");
         $listing_form.attr('disabled', 'disabled');
         $('#id_random_sample_label-control-group').hide();
     }

 }


 function init_fields() {
    //this depends on awesomplete js
     toggle_random_label = function() {
        if($('#id_listing_form').val())
            $('#id_random_sample_label-control-group').show();
        else {
            $('#id_random_sample_label-control-group').hide();
            $('#id_random_sample_label').val('');
         }
    };
     $('#id_preferred_listing').change(function(){
        if($(this).val()){
             $('#id_listing_form').val('');
             $('#id_listing_form-control-group').hide();
        }
        else{
            $('#id_listing_form-control-group').show();
        }
    });
    toggle_random_label();
    $('#id_listing_form').change(function(){
            toggle_random_label();
            $('#id_random_sample_label').val('');
    });
 }

 jQuery(function($){
     show_or_hide_sample_size();
     $('input[name=has_sampling]').on('change', function(){
         show_or_hide_sample_size();
     });
 });

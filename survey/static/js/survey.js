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
     $("#id_listing_form").append($('<option value="val"/>').text('--Select Listing Form--'));
    $("#id_listing_form").val("val");
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


 function init_fields(fetch_qset_ids_url) {
    //this depends on awesomplete js
     toggle_random_label = function() {
        if($('#id_listing_form').val())
            $('#id_random_sample_label-control-group').show();
        else
            $('#id_random_sample_label-control-group').hide();
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
    var random_label = document.querySelector("#id_random_sample_label");
    var aucomplete = null;
    $('#id_listing_form').change(function(){
            toggle_random_label();
            $.get( fetch_qset_ids_url+ "?id=" + $('#id_listing_form').val(), function( list ) {

                $(random_label).val('');
                if(aucomplete){             // need to find a better way to remove this
                   aucomplete.filter = null;
                   aucomplete.replace = null;
                   aucomplete.list = [];
                   aucomplete = null;
                }

                aucomplete = get_autocomplete(list);
            });
    });

    $(random_label).on('keydown', function() {
         if (this.value.length > 1 && aucomplete == null) {
              $.get( fetch_qset_ids_url+ "?id=" + $('#id_listing_form').val(), function( list ) {
                aucomplete = get_autocomplete(list);
            });
         }
    });

    get_autocomplete = function(list) {
            return new Awesomplete(random_label, {
                                    list: list,
                                        filter: function(text, input) {
                                            return Awesomplete.FILTER_CONTAINS(text, input.match(/[^{{]*$/)[0]);
                                        },

                                        replace: function(text) {
                                            var before = this.input.value.match(/^.*{{\s*|/)[0];
                                            this.input.value = before +text + "}} ";
                                        }
                                });
    }

 }

 jQuery(function($){
     show_or_hide_sample_size();
     $('input[name=has_sampling]').on('change', function(){
         show_or_hide_sample_size();
     });
 });

 ;

 jQuery(function($){
    $('#id_has_sampling').on('change', function(){
        var $idsamplesize = $('#id_sample_size');
        var $div_to_toggle = $idsamplesize.closest('div').parent('div');

        if ($(this).is(':checked')){
            $div_to_toggle.show()
            }
        else{
            $div_to_toggle.hide();
            $idsamplesize.val(0)
        }
    });
 });

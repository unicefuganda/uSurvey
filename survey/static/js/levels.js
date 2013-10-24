
;

$(function(){
    var $form = $("#hierarchy-form"),
        $total_forms=$("#id_form-TOTAL_FORMS"),
        template = $("#add-level-template").html();

    function assignLevelNumbers(){
        $form.find("span.number").each(function(i, element){
            $(element).text(++i);
        });
    }

    function assignFormFieldsNames(){
        var $all_rows = $form.find("tr");
         $all_rows.each(function(i, row){
             $(row).find("input").each(function(j, element){
                var $element = $(element),
                    name = $element.attr('name').split('-').pop();
                $element.attr('name', 'form-'+ i + '-' + name);
             });
         });
        $total_forms.val($all_rows.length);
    }

    function AdjustLevelAndNames(){
        assignLevelNumbers();
        assignFormFieldsNames();
        toggleCodeField();
    }

    $form.on("click", ".add-level", function(){
        $(this).parents("tr").after(template);
        AdjustLevelAndNames();
    });

    $form.on("click", ".remove-level", function(){
        $(this).parents("tr").remove();
        AdjustLevelAndNames();
    });

    function toggleCodeField(){
        $(".has_code").on("change", function(){
            var $code_field = $(this).parents("tr").find(".code");
            $(this).is(':checked') ? $code_field.show() : $code_field.hide();
        });
    }

    toggleCodeField();

});


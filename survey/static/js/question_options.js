
;

jQuery(function($){

    var $form = $(".question-form"),
        template = $("#question-option-template").html();

    function assignOptionNumbers(){
        $form.find("span.number").each(function(i, element){
            $(element).text(++i);
        });
    }

    function addQuestionOption($element){
        $element.after(template);
        assignOptionNumbers();
    }

    $("#id_answer_type").on('change', function(){
        if($(this).val() == 'multichoice'){
            addQuestionOption($(this).parents("div.control-group"));
        }else{
            $form.find("div.question-option").remove();
        };
    });

    $form.on("click", ".add-option", function(){
        addQuestionOption($(this).parents("div.question-option"));
    });

    $form.on("click", ".remove-option", function(){
        $(this).parents("div.question-option").remove();
        assignOptionNumbers();
    });

    var group_select_template = $("#question-group-template").html();
    replaceQuestionGroupSelect(group_select_template);

    function replaceQuestionGroupSelect(template){
      if(!$.isEmptyObject(template)){
        $('#id_group').replaceWith(template);
      };
    };

});

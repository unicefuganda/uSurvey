
;

$(function(){
    var $form = $("#hierarchy-form"),
    template = $("#option-template").html(),
    addOptionIcon = '<a href="javascript:;" class="add-on btn btn_primary add-option"><i class="icon-plus"></i></a>'


    function assignOptionNumbers(){
        $form.find("span.number").each(function(i,element){
            $(element).text(i+2);
        });

    }

    function addQuestionOption($element){
        $element.after(template);
        assignOptionNumbers();
    }
    function appendAddOptionIcon(element){
        element.before(addOptionIcon);
    }
    appendAddOptionIcon($("#id_levels").next());

    $form.on("click", ".add-option", function(){
        addQuestionOption($("div.control-group").last());
    });

    $form.on("click", ".remove-option", function(){
        $("div.control-group").last().remove();
        assignOptionNumbers();
    });
});

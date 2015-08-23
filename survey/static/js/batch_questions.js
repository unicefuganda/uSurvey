;
function modify_input_names() {
    var first_row = $('#questions_table').children().last().find('tr').first();
    var first_row_input = first_row.find("input[name=order_information]");

    var counter = 1;

    while (first_row_input.val()) {
        var new_name_value = counter.toString() + '-' + first_row_input.val().split('-')[1];
        first_row_input.val(new_name_value);

        first_row = first_row.next();
        first_row_input = first_row.find("input[name=order_information]");
        counter = counter + 1;
    }
}
jQuery(function($){
    $(".table").tableDnD({
        onDrop: function(){
            modify_input_names();
        },
        onEnd: function(){
            modify_input_names();
        }
    });

});
;
$(".modal-body button[name='save_condition_button']").on('click', function (e) {
    if (validate_condition_form()) {

        $.ajax({
            url: '/conditions/new/',
            type: 'POST',
            data: $(".modal-body form").serialize(),
            success: function (response) {
                $('.alert-success').remove()
                $('#id_conditions').append("<option value='" + response.id + "'>" + response.value + "</option>");
                $('.multi-select').multiSelect('refresh');
                $("#content").prepend("<div class='alert alert-success'> <ul>Condition successfully added.</ul></div>")
            }
        });
    }

    return false;
});

function clear_fields() {
    var form_fields = get_form_fields();
    form_fields.forEach(function (field) {
        field.val("")
        field.next().text("")
    })
}

function set_or_clear(field, set) {
    if (set) {
        field.next().text("This field is required.");
    }
    else {
        field.next().text("");
    }
}
function clear_error_messages(form_fields) {
    form_fields.forEach(function (field) {
        set_or_clear(field, false)
    })
}

function set_error_messages(form_fields) {
    form_fields.forEach(function (field) {
        if (field.val().trim().length == 0) {
            set_or_clear(field, true)
        }
    })
}

function get_form_fields() {
    var value_field_value = $('.modal-body form #id_value')

    var form_fields = Array()
    form_fields.push(value_field_value)

    return form_fields
}

function validate_condition_form() {

    var is_valid = false

    var form_fields = get_form_fields();

    if (form_fields[0].val().trim().length != 0) {
        $('.modal').modal('toggle');
        return true
    }

    clear_error_messages(form_fields);
    set_error_messages(form_fields);
    return is_valid
}
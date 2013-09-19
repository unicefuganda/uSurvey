;
$(function(){
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
                    $("#content").prepend("<div class='alert alert-success'> <ul>Condition successfully added.</ul></div>");
                }
            });
        };

        return false;
    });

    function set_or_clear(field, set) {
        if (set) {
            field.next().text("This field is required.");
        }else {
            field.next().text("");
        };
    };
    
    function clear_error_messages(form_fields) {
        form_fields.forEach(function (field) {
            set_or_clear(field, false);
        });
    };

    function set_error_messages(form_fields) {
        form_fields.forEach(function (field) {
            if (field.val().trim().length == 0) {
                set_or_clear(field, true);
            };
        });
    };

    function validate_condition_form() {
        var is_valid = false,
            form_fields = get_form_fields();
        if (form_fields[0].val().trim().length != 0) {
            $('.modal').modal('toggle');
            return true;
        };
        clear_error_messages(form_fields);
        set_error_messages(form_fields);
        return is_valid;
    };

    var gender_select_template = $('#gender_value_select_template').html(),
        age_select_template =$('#age_value_select_template').html(),
        general_select_template =$('#general_value_select_template').html();
        
    var condition = $('#id_condition'),
        original_conditions = condition.html(),
        equal_only_condition = '<option value="EQUALS">EQUALS</option>';

    function switch_condition(condition_option){
        condition.find('option')
            .remove()
            .end()
            .append(condition_option)
            .val('EQUALS');
    };

    $('#id_attribute').on('change', function(){
        var value = $('#id_value');
        value.focus();
        var attribute = $(this).val();        
        if (attribute == 'GENDER'){
            switch_condition(equal_only_condition);
            value.replaceWith(gender_value_select_template.innerHTML);
            return true;
        };
        if (attribute == 'AGE'){
            switch_condition(original_conditions);
            value.replaceWith(age_value_select_template.innerHTML);
                
            return true;
        };
        if (attribute == 'GENERAL'){
            switch_condition(equal_only_condition);
            value.replaceWith(general_value_select_template.innerHTML);
            return true;
        };
    });

    jQuery.validator.addMethod("positive_if_age", function(value, element) {
          $(element).next().text("")
          attribute_value = $('#id_attribute').val()
          if (attribute_value == 'AGE'){
              return value > 0;
          }
          return true;
        }, "Age cannot be negative.");
    
    $('#add-condition-form').validate({
        rules: {
          'attribute': 'required',
          'condition':'required',
          'value': {required:true, positive_if_age:true}
        },
    });
    
});

// global context

function clear_fields() {
    var form_fields = get_form_fields();
    form_fields.forEach(function (field) {
        field.val("")
        field.next().text("")
    });
};

function get_form_fields() {
    var value_field_value = $('.modal-body form #id_value'),
        form_fields = Array()
    form_fields.push(value_field_value);
    return form_fields;
};

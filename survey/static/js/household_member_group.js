;
$(function(){

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
    
    function adjust_field(attribute, value){
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
    };

    $('#id_attribute').on('change', function(){
        adjust_field($(this).val(), $('#id_value'));
        $('#id_value').click();
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
        submitHandler: function(form, e){
            e.preventDefault()
            form = $(form);
            $.post(form.attr('action'), form.serializeArray(), function(data){
                    window.location.reload();
            });
            return true;
        }
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

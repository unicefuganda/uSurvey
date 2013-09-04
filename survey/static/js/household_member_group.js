;
$(".modal-body button[name='save_condition_button']").on('click', function(e){
    $.ajax({
           url: '/conditions/new/',
           type: 'POST',
           data: $(".modal-body form").serialize(),
           success: function(response){
            $('.modal').modal('toggle');
               $('#condition').append("<option value='"+response.id +"'>"+ response.value +"</option>");
               $("#content").prepend("<div class='alert alert-success'> <ul>Condition successfully added.</ul></div>")
           }
       });

       return false;
});

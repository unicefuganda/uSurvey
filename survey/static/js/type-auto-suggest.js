$(function(){
    antsmc2__aucomplete = null;
    });

function make_suggestions(elem_selector, fetch_qset_ids_url) {
    var elem = document.querySelector(elem_selector);
    if (new RegExp("^.*\{\{\s*$").test(elem.value)) {
          $.get( fetch_qset_ids_url, function( list ) {
            if(antsmc2__aucomplete){
               antsmc2__aucomplete._list = list;
               antsmc2__aucomplete.evaluate();
             }
             else
                antsmc2__aucomplete = get_autocomplete(list);
        });
     }

    get_autocomplete = function(list) {
            return new Awesomplete(elem, {
                                    list: [],
                                        filter: function(text, input) {
                                            return Awesomplete.FILTER_CONTAINS(text, input.match(/[^({{)]*$/)[0]);
                                        },

                                        replace: function(text) {
                                            var before = this.input.value.match(/^.*{{\s*|/)[0].trim();
                                            this.input.value = before +text + "}} ";
                                        }
                                });
    }

}





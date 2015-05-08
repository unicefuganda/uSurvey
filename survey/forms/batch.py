from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from survey.models import BatchQuestionOrder
from survey.models.batch import Batch
from django.utils.safestring import mark_safe

from survey.models.formula import *


class TableRowForm(forms.Form):
    '''
    This form is special, because usually, forms include a range of inputs
    to be filled out by the user. This form however, no inputs are filled in. The
    form is given a queryset of objects and a list of field names, and with those,
    a table is made. Each row in the table represents an object. clicking a row
    will select the object. Multiple submit buttons can be given with various
    functions. What these buttons have in common is that they all operate on the
    selected objects, e.g. selecting three objects and pressing delete will delete
    those three objects. The form is different in that it does not create new objects,
    it manipulates already existing objects.
    '''
    def __init__(self, queryset, fields):
        if not fields:
            raise Exception('A TableRowForm must be supplied both queryset and fields')
        self.queryset = queryset
        self.fields = fields

    def __unicode__(self):
        '''
        Builds the html table rows for the form.
        '''
        if not self.queryset: return '<tr><td>No data...<td></tr>'
        colcount = 0
        res = ''
        res += '<div class="batchQuestions"><table id="table1" class="dataTable display"><thead>'
        for f in self.fields:
            res += "<th>"+self.queryset[0]._meta.get_field_by_name(f)[0].verbose_name.upper()+"</th>"
        res += "</thead><tbody>\n"
        for obj in self.queryset:
            res += '<tr id="%s-selectable" class="ms-selectable" onclick="selectRow(this)">' % obj.pk
            res += '<td><input style="display:none;" type="checkbox" name="slct" id="%s" value="%s"/>'%(obj.pk,obj.pk)

            vals = [getattr(obj, x) for x in self.fields]
            colcount = len(vals)
            for x in vals:
                res += '%s</td><td>'%(x.encode('ascii', 'ignore'))
            res = res[:-4]
            res += '</tr>\n'
        res += '</tbody></table>'
        res += '<div class="answer"><br /><h3>Selected Questions</h3><table id="table2" class="dataTable display"><thead>'
        for f in self.fields:
            res += "<th>"+self.queryset[0]._meta.get_field_by_name(f)[0].verbose_name.upper()+"</th>"
        res += "</thead><tbody></tbody></table></div>\n"
        
        res += '''\
        <script>
        // Allows for selectable tablerows in forms
        function selectRow(row)
        {
            // Check/uncheck the checkbox
            var chk = row.getElementsByTagName('input')[0];
            chk.checked = !chk.checked;
        }
        </script>'''
        res += '''
                
                <script src="/static/jquery-1.11.1.min.js"></script>
                <script src="/static/jquery.dataTables.min.js" type="text/javascript"></script>

                <link href="/static/jquerysctipttop.css" rel="stylesheet" type="text/css">
                <link href="/static/jquery.dataTables.min.css" rel="stylesheet" type="text/css">
                <link href="/static/jquery.dataTables.css" rel="stylesheet" type="text/css">
                
                
                <link href="/static/bootstrap.min.css" type="text/css" rel="stylesheet">
                <script type="text/javascript">
                
                
                
                $(document).ready(function() {
                    table1 = $('#table1').DataTable( { paging: false, scrollY: 300,  "order": [[ 1, "asc" ]]});
                    table2 = $('#table2').DataTable( { paging: false, scrollY: 300, "order": [[ 1, "asc" ]]});
                    //table = $('#table1').DataTable( { 'ajax' : get_question_url()});
                    //var table2 = $('#table2').DataTable();
                  
                    table1.on( 'click', 'tr', function () {
                        var row = table1.row($(this));
                        var rowNode = row.node();
                        row.remove();
 
                        table2
                            .row.add( rowNode )
                            .draw();
                        chk = rowNode.getElementsByTagName('input')[0];
                        chk.checked = true;
                    } );   
                    table2.on( 'click', 'tr', function () {
                        var row = table2.row($(this));
                        var rowNode = row.node();
                        row.remove();
 
                        table1
                            .row.add( rowNode )
                            .draw();
                        chk = rowNode.getElementsByTagName('input')[0];
                        chk.checked = false;
                    } ); 
                     
                } );
                function reload_question_data() {
                    var group_selected = $('#assign_question_group').val();
                    var module_selected = $('#assign_module').val();
                    var batch_id = $("#batch_id").val();
                    q_url = '/batches/' + batch_id + '/questions/groups/' + group_selected + '/module/' + module_selected + '/';
                    var jsonData;
                    $.getJSON(q_url, function (data) { 
                    $('#table1 .ms-selectable').hide();
                    $.each(data, function (key, value) {
                            $('#' + value.id + '-selectable').show();
                        });
                    });
                    return jsonData;
                      
                }
                
                $('#assign_question_group').on('change', function () {
                    reload_question_data();
                    
                });
                $('#assign_module').on('change', function () {
                    reload_question_data();
                    
                });
                </script>
                <style type="text/css">
                    div.span6 {
                        display: block;
                        float: left;
                    }
                    #table1_length label, #table1_filter label {
                        display: block;
                        width: 1000px;
                        float: left;
                    }
                    
                    #table1_length, #table1_filter {
                      display: block;
                      width: 100%;
                    }
                    #table2_length label, #table2_filter label {
                        display: block;
                        width: 1000px;
                        float: left;
                    }
                    
                    #table2_length, #table2_filter {
                      display: block;
                      width: 100%;
                    }
                    div.span6 input, div.span6 select {
                        //float: right;
                        border-left: None;
                        
                    }
                    
                    
                </style>
                </div>'''
        return res


class BatchForm(ModelForm):

    class Meta:
        model = Batch
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={"rows": 4, "cols": 50})
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        existing_batches = Batch.objects.filter(name=name, survey=self.instance.survey)
        if existing_batches.count() > 0 and self.initial.get('name', None) != str(name):
            raise ValidationError('Batch with the same name already exists.')
        return self.cleaned_data['name']


class BatchQuestionsForm(ModelForm):
    questions = forms.ModelMultipleChoiceField(label=u'', queryset=Question.objects.filter(subquestion=False).exclude(group__name='REGISTRATION GROUP'),
                                               widget=forms.SelectMultiple(attrs={'class': 'multi-select'}))

    class Meta:
        model = Batch
        fields = ['questions']

    def __init__(self, batch=None, *args, **kwargs):
        super(BatchQuestionsForm, self).__init__(*args, **kwargs)
        self.fields['questions'].queryset = Question.objects.filter(subquestion=False).exclude(group__name='REGISTRATION GROUP').exclude(batches=batch)

    def save_question_to_batch(self, batch):
        for question in self.cleaned_data['questions']:
            question.save()
            order = BatchQuestionOrder.next_question_order_for(batch)
            BatchQuestionOrder.objects.create(question=question, batch=batch, order=order)
            question.batches.add(batch)

    def save(self, commit=True, *args, **kwargs):
        batch = super(BatchQuestionsForm, self).save(commit=commit, *args, **kwargs)

        if commit:
            batch.save()
            self.save_question_to_batch(batch)

class TableBatchQuestionsForm(TableRowForm):
#    questions = TableRowForm(queryset=Question.objects.filter(subquestion=False).exclude(group__name='REGISTRATION GROUP'), fields=('identifier', 'text', 'answer_type')

#forms.ModelMultipleChoiceField(label=u'', queryset=Question.objects.filter(subquestion=False).exclude(group__name='REGISTRATION GROUP'),
#                                               widget=forms.SelectMultiple(attrs={'class': 'multi-select'}))

    def __init__(self, batch=None, *args, **kwargs):
        super(TableBatchQuestionsForm, self).__init__(queryset=Question.objects.filter(subquestion=False).exclude(group__name='REGISTRATION GROUP', batches=batch), fields=( 'identifier', 'text', ))
        self.questions = Question.objects.filter(subquestion=False).exclude(group__name='REGISTRATION GROUP').exclude(batches=batch)
        if kwargs.get('data', None):
            self.questions = self.questions.filter(pk__in=kwargs.get('data').getlist('slct'))
        self.batch = batch

    def is_valid(self):
        return True

    def save_question_to_batch(self, batch):
        for question in self.questions:
            order = BatchQuestionOrder.next_question_order_for(batch)
            BatchQuestionOrder.objects.create(question=question, batch=batch, order=order)
            question.batches.add(batch)

    def save(self, *args, **kwargs):
        batch = self.batch
        self.save_question_to_batch(batch)

from django.contrib.auth.decorators import permission_required
from survey.models import ListingTemplate
from .question_set import QuestionSetView


@permission_required('auth.can_view_batches')
def index(request):
    return QuestionSetView(model_class=ListingTemplate).index(request, ListingTemplate.objects.all())


@permission_required('auth.can_view_batches')
def new(request):
    request.breadcrumbs(ListingTemplate.new_breadcrumbs())
    return QuestionSetView(model_class=ListingTemplate).new(request)


@permission_required('auth.can_view_batches')
def edit(request, qset_id):
    request.breadcrumbs(ListingTemplate.edit_breadcrumbs())
    return QuestionSetView(model_class=ListingTemplate).edit(request, ListingTemplate.get(pk=qset_id))


@permission_required('auth.can_view_batches')
def delete(request, qset_id):
    return QuestionSetView(model_class=ListingTemplate).delete(request, ListingTemplate.get(pk=qset_id))





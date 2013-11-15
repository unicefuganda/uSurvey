from celery.task import task


@task
def upload_task(upload_form):
    return upload_form.upload()

class UserFilterViewMixin:
    def get_queryset(self):
        duser_id = self.request.session.get('duser_id')
        return self.model.objects.by_duser(duser_id=duser_id)

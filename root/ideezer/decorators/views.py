from django.utils.decorators import method_decorator


def paginated_cbv(*args, **kwargs):
    PAGINATE_BY = 20
    PAGINATE_ORPHANS = 4

    if args and callable(args[0]):
        klass = args[0]
        klass.paginate_by = PAGINATE_BY
        klass.paginate_orphans = PAGINATE_ORPHANS
        return klass

    def _inner(klass):
        klass.paginate_by = kwargs.get('paginate_by', PAGINATE_BY)
        klass.paginate_orphans = kwargs.get('paginate_orphans', PAGINATE_ORPHANS)
        return klass

    return _inner


def decorate_cbv(decorator_or_decorators):
    def _inner(klass):
        if isinstance(decorator_or_decorators, (list, tuple)):
            decorators = decorator_or_decorators
        else:
            decorators = (decorator_or_decorators, )

        for decorator in decorators:
            klass.dispatch = method_decorator(decorator)(klass.dispatch)

        return klass
    return _inner

from threading import local

_thread_locals = local()


def get_current_session():
    return getattr(_thread_locals, 'session', None)

def get_current_user():
    return getattr(_thread_locals, 'user', None)

def get_current_ip():
    return getattr(_thread_locals, 'ip', None)


def get_current_request():
    return getattr(_thread_locals, 'request', None)


class ThreadLocals:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        _thread_locals.user = getattr(request, 'user', None)
        _thread_locals.session = getattr(request, 'session', None)
        _thread_locals.ip = request.META.get('HTTP_X_FORWARDED_FOR')
        response = self.get_response(request)

        return response

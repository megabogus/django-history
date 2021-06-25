=======
History
=======

History is a Django app to log change model fields

Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "django_history" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'django_history',
        ...
    ]

2. Add middleware to your MIDDLEWARE::

    MIDDLEWARE = [
        ...
        'django_history.middleware.ThreadLocals',
    ]

3. Add models fields to your OBSERVED_FIELDS::

    OBSERVED_FIELDS = {
        'accounts.User':
                (
                      'username', 'first_name', 'middle_name', 'last_name', 'gender', 'phone', 'email',
                      'photo', 'birthday',
                ),
        ...
    }

4. Use to admin.py::

    from django.contrib import admin
    from django_history.admin import HistoryBlockAdmin

    @admin.register(App)
    class AppAdmin(HistoryBlockAdmin, admin.ModelAdmin):
        ...

5. Run ``python manage.py migrate`` to create the history models.

6. Start the development server and visit http://127.0.0.1:8000/admin/
   to create a history (you'll need the Admin app enabled).

7. Visit http://127.0.0.1:8000/admin/django_history/action/ to participate in the all history.

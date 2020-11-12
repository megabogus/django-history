=======
History
=======

|build-status| |coverage| |license| |wheel| |pyversion| |pyimp| |ocbackerbadge| |ocsponsorbadge|

History is a Django app to log change models fields

Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "history" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'history',
        ...
    ]

2. Add middleware to your MIDDLEWARE::

   MIDDLEWARE = [
        ...
        'history.middleware.ThreadLocals',
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

4. Run ``python manage.py migrate`` to create the polls models.

5. Start the development server and visit http://127.0.0.1:8000/admin/
   to create a history (you'll need the Admin app enabled).

6. Visit http://127.0.0.1:8000/admin/history/action/ to participate in the all history.

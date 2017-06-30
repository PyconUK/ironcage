from django.core import mail
from django.core.mail import get_connection
from django.utils.log import AdminEmailHandler as DjangoAdminEmailHandler


class AdminEmailHandler(DjangoAdminEmailHandler):
    def send_mail(self, subject, message, *args, **kwargs):
        kwargs['fail_silently'] = False
        mail.mail_admins(subject, message, *args, connection=self.connection(), **kwargs)

    def connection(self):
        return get_connection(backend=self.email_backend, fail_silently=False)

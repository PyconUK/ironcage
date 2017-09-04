from django.core.mail import get_connection, EmailMultiAlternatives


def send_mail(subject, message, to_addr):
    connection = get_connection()

    mail = EmailMultiAlternatives(
        subject,
        message,
        'noreply@pyconuk.org',
        [to_addr],
        reply_to=['pyconuk-committee@uk.python.org']
        connection=connection
    )

    return mail.send()

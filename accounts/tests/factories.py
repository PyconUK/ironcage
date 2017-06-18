from accounts.models import User


def create_user(name='Alice', **kwargs):
    email_addr = f'{name.lower()}@example.com'
    return User.objects.create_user(email_addr=email_addr, name=name, **kwargs)

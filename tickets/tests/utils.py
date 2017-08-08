from django.http import QueryDict


def build_querydict(data):
    qd = QueryDict('', mutable=True)
    for key, value in data.items():
        if isinstance(value, list):
            for v in value:
                qd.update({key: v})
        else:
            qd.update({key: value})
    qd._mutable = False
    return qd

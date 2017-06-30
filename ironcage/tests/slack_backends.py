from django_slack.utils import Backend


class TestBackend(Backend):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset_messages()

    def send(self, url, data, **kwargs):
        self.messages.append(data)

    def reset_messages(self):
        self.messages = []

    def retrieve_messages(self):
        messages = self.messages
        self.reset_messages()
        return messages

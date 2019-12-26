from django.apps import AppConfig


class EntriesConfig(AppConfig):
    name = "entries"

    def ready(self):
        import entries.signals

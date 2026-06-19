from django.apps import AppConfig


class HrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hr'

    def ready(self):
        try:
            from hr.scheduler import start_scheduler
            start_scheduler()
        except ImportError:
            pass

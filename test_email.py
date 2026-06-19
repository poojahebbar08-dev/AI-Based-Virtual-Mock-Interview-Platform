import os
import django
from django.conf import settings
from django.core.mail import send_mail

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_interview_platform.settings')
django.setup()

try:
    send_mail(
        subject='Test Subject',
        message='Test Message',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['poojahebbar12@gmail.com'],
        fail_silently=False,
    )
    print("Email sent successfully")
except Exception as e:
    import traceback
    traceback.print_exc()

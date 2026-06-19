import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from datetime import timedelta
from ai_interview_platform.utils.email_service import send_brevo_email
from hr.models import HRInterviewBooking

logger = logging.getLogger(__name__)

def check_upcoming_interviews():
    now = timezone.now()
    
    # Get all scheduled bookings that haven't sent a reminder
    bookings = HRInterviewBooking.objects.filter(
        status='scheduled',
        reminder_sent=False
    )
    
    for booking in bookings:
        # Combine date and start_time
        from datetime import datetime
        meeting_datetime = timezone.make_aware(
            datetime.combine(booking.time_slot.date, booking.time_slot.start_time),
            timezone.get_current_timezone()
        )
        
        time_diff = meeting_datetime - now
        minutes_until = int(time_diff.total_seconds() / 60)
        
        # If the interview is starting in <= 10 minutes, and is not in the past
        if 0 < minutes_until <= 10:
            send_reminder_email(booking, minutes_until)
            booking.reminder_sent = True
            booking.save(update_fields=['reminder_sent'])

def send_reminder_email(booking, minutes_until):
    candidate_email = booking.candidate.email
    hr_name = booking.hr.full_name
    
    # Get candidate name
    candidate_name = booking.candidate.get_full_name() or booking.candidate.username
    try:
        from candidate.models import CandidateProfile
        profile = CandidateProfile.objects.get(user=booking.candidate)
        if profile.name:
            candidate_name = profile.name
    except Exception:
        pass

    date_str = booking.time_slot.date.strftime('%B %d, %Y')
    start_str = booking.time_slot.start_time.strftime('%I:%M %p')
    
    subject = f"Reminder: Your HR Interview starts in {minutes_until} minutes!"
    message = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <h2 style="color: #2c3e50;">Interview Reminder</h2>
        <p>Hello {candidate_name},</p>
        <p>This is a friendly reminder that your <strong>HR Interview</strong> with <strong>{hr_name}</strong> will start in <strong>{minutes_until} minutes</strong>.</p>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #007bff;">
            <h3 style="margin-top: 0; color: #007bff;">Meeting Details</h3>
            <p><strong>Candidate Name:</strong> {candidate_name}</p>
            <p><strong>Interview Type:</strong> HR Interview</p>
            <p><strong>Interview Date:</strong> {date_str}</p>
            <p><strong>Interview Time:</strong> {start_str}</p>
            <p><strong>Meeting ID / Room Code:</strong> {booking.meeting_id}</p>
            <p><strong>Password:</strong> {booking.meeting_password}</p>
            <p style="margin-bottom: 0;"><strong>Meeting URL:</strong> <br>
               <a href="{booking.meeting_url}" style="display: inline-block; margin-top: 10px; padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px;">Join Interview</a>
            </p>
            <p><small>(You can also copy this URL: {booking.meeting_url})</small></p>
        </div>
        
        <p>Please make sure you are in a quiet environment and your camera and microphone are working.</p>
        <p>Best of luck!<br>IntervAI Team</p>
    </div>
    """
    
    try:
        success = send_brevo_email(candidate_email, subject, message)
        if success:
            print(f"Sent 10-min reminder email to {candidate_email}")
        else:
            print(f"Failed to send 10-min reminder email to {candidate_email}")
    except Exception as e:
        logger.error(f"Failed to send reminder email to {candidate_email}: {e}")

def start_scheduler():
    # To prevent duplicate schedulers when running with Django's auto-reloader
    if os.environ.get('RUN_MAIN', None) != 'true':
        return
        
    scheduler = BackgroundScheduler()
    # Check every minute
    scheduler.add_job(check_upcoming_interviews, 'interval', minutes=1)
    scheduler.start()
    print("Background scheduler started for interview reminders.")

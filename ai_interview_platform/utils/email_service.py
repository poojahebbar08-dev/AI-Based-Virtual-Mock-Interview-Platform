from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags

def send_brevo_email(to_email, subject, html_content):
    """
    Function is named 'send_brevo_email' for compatibility with existing code,
    but it now uses standard Django SMTP to send emails.
    """
    text_content = strip_tags(html_content)
    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            html_message=html_content,
            fail_silently=False,
        )
        print(f"✅ EMAIL SENT: To {to_email} | Subject: {subject}")
        return True
    except Exception as e:
        print(f"❌ EMAIL FAILED: To {to_email} | Error: {str(e)}")
        print(f"   Using EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"   Check your .env file for correct EMAIL_HOST_PASSWORD.")
        return False

def send_job_recommendation_email(to_email, jobs_data):
    """
    Send an HTML email containing job recommendations to the candidate.
    """
    subject = "Your Personalized Job Recommendations"
    
    # Build HTML for jobs
    jobs_html = ""
    for job in jobs_data:
        jobs_html += f"""
        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 15px; background-color: #fdfdfd;">
            <h3 style="margin: 0 0 5px 0; color: #ff385c;">{job.get('title')}</h3>
            <p style="margin: 0 0 10px 0; font-weight: 500;">{job.get('company')} - {job.get('location')}</p>
            <div style="display: flex; gap: 15px; margin-bottom: 15px; font-size: 14px; color: #666;">
                <span>💰 {job.get('salary')}</span>
                <span>⏱️ {job.get('type')}</span>
                <span>📅 Posted {job.get('posted')}</span>
            </div>
            <a href="{job.get('source_url')}" style="background-color: #28a745; color: #fff; text-decoration: none; padding: 8px 16px; border-radius: 6px; font-size: 14px; font-weight: bold; display: inline-block;">Apply Now</a>
        </div>
        """
        
    html_content = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="color: #ff385c; margin-bottom: 10px;">Great Job on Your Interview! 🎉</h1>
            <p style="font-size: 16px; color: #555;">Based on your recent performance and skills, we've found some excellent opportunities for you.</p>
        </div>
        
        <div style="margin-top: 10px;">
            <h2 style="border-bottom: 2px solid #ff385c; padding-bottom: 10px; margin-bottom: 20px;">Recommended Roles</h2>
            {jobs_html}
        </div>
        
        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #888; font-size: 12px;">
            <p>Keep up the good work and best of luck with your applications!</p>
            <p>AI Interview Platform Team</p>
        </div>
    </div>
    """
    
    return send_brevo_email(to_email, subject, html_content)

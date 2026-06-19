from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
import string
from ai_interview_platform.supabase_storage import SupabaseStorage


class CandidateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Store resumes locally by default
    resume = models.FileField(
        upload_to='resumes/',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)  # Full Name
    dob = models.DateField(null=True, blank=True)
    field = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    preferred_language = models.CharField(max_length=50, default='English')

    def __str__(self):
        return self.user.username

class EmailConfirmationOTP(models.Model):
    """OTP for email confirmation during registration"""
    email = models.EmailField()
    otp = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.email} - {self.otp}"
    
    def is_expired(self):
        """Check if OTP has expired (10 minutes)"""
        expiry_time = self.created_at + timedelta(minutes=10)
        return timezone.now() > expiry_time
    
    def generate_otp(self):
        """Generate a new 4-digit OTP"""
        self.otp = ''.join(random.choices(string.digits, k=4))
        self.save()
        return self.otp
    
    @classmethod
    def create_otp(cls, email):
        """Create or update OTP for an email"""
        # Delete any existing unused OTPs for this email
        cls.objects.filter(email=email, is_used=False).delete()
        
        # Create new OTP
        otp_instance = cls.objects.create(email=email)
        otp_instance.generate_otp()
        return otp_instance

class PasswordResetOTP(models.Model):
    """OTP for password reset"""
    email = models.EmailField()
    otp = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.email} - {self.otp}"
    
    def is_expired(self):
        """Check if OTP has expired (10 minutes)"""
        expiry_time = self.created_at + timedelta(minutes=10)
        return timezone.now() > expiry_time
    
    def generate_otp(self):
        """Generate a new 4-digit OTP"""
        self.otp = ''.join(random.choices(string.digits, k=4))
        self.save()
        return self.otp
    
    @classmethod
    def create_otp(cls, email):
        """Create or update OTP for an email"""
        # Delete any existing unused OTPs for this email
        cls.objects.filter(email=email, is_used=False).delete()
        
        # Create new OTP
        otp_instance = cls.objects.create(email=email)
        otp_instance.generate_otp()
        return otp_instance
    
class InterviewRecord(models.Model):
    """Persistent record of an AI interview for analytics and history."""
    candidate = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    evaluations = models.JSONField(default=list)
    average = models.FloatField(default=0)
    total_questions = models.IntegerField(default=0)
    answered_questions = models.IntegerField(default=0)
    skipped_questions = models.IntegerField(default=0)
    difficulty_level = models.CharField(max_length=20, default='medium', choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('advanced', 'Advanced')
    ])
    career_advice = models.TextField(blank=True, null=True)
    
    # Biometric Data Fields
    bio_happy = models.IntegerField(default=0)
    bio_sad = models.IntegerField(default=0)
    bio_angry = models.IntegerField(default=0)
    bio_fearful = models.IntegerField(default=0)
    bio_disgusted = models.IntegerField(default=0)
    bio_surprised = models.IntegerField(default=0)
    bio_neutral = models.IntegerField(default=0)
    bio_total_frames = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Interview {self.id} - {self.candidate.email} - {self.designation}"
        
class RecommendedJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommended_jobs')
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    source = models.CharField(max_length=100)
    source_url = models.URLField(max_length=1000)
    description = models.TextField(blank=True, null=True)
    salary = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(max_length=50, blank=True, null=True)
    posted = models.CharField(max_length=50, blank=True, null=True)
    match_percentage = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} at {self.company} ({self.status})"
        
    @property
    def is_available(self):
        return bool(self.source_url) and self.source_url != "#"
from django.db import models
from django.contrib.auth.models import AbstractUser

class Admin(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Admin"
        verbose_name_plural = "Admins"

class SystemSettings(models.Model):
    require_job_approval = models.BooleanField(default=True, help_text="Require admin approval before sending job recommendation emails")
    
    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"
        
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SystemSettings.objects.exists():
            return SystemSettings.objects.first()
        return super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj

class JobRecommendationQueue(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    candidate = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='job_recommendations')
    interview_type = models.CharField(max_length=50, choices=[('mock', 'Mock Interview'), ('hr', 'HR Interview')])
    interview_id = models.IntegerField(help_text="ID of the related interview record")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    jobs_data = models.JSONField(help_text="JSON list of recommended jobs")
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Job Recs for {self.candidate.username} ({self.status})"

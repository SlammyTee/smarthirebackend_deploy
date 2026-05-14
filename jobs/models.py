import uuid
from pgvector.django import VectorField
from django.db import models
from useraccounts.models import User

class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.JSONField(default=list, blank=True)

    skills = models.JSONField(default=list, blank=True)  # List of required skills
    embedding = VectorField(dimensions=384, null=True, blank=True)  # For AI ranking

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Application(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Shortlisted', 'Shortlisted'),
        ('Rejected', 'Rejected'),
        ('Interview Invited ', 'Interview Invited'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE , related_name="applications")  

    resume = models.FileField(upload_to='resumes/')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    score = models.FloatField(null=True, blank=True)  # AI ranking score

    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "job") 

    def __str__(self):
        return f"{self.user.username} - {self.job.title}"
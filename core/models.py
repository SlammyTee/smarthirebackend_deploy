from django.db import models
from useraccounts.models import User

# Create your models here.
class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ("Created Job", "Created Job"),
        ("Updated Job", "Updated Job"),
        ("Deleted Job", "Deleted Job"),
        ("Applied", "Applied"),
        ("Shortlisted Candidate", "Shortlisted Candidate"),
        ("Rejected Candidate", "Rejected Candidate"),
        ("Scheduled Interview", "Scheduled Interview"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    action = models.CharField(
        max_length=100,
        choices=ACTION_CHOICES
    )

    details = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.action}"
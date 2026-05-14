from rest_framework import serializers
from .models import Application, Job
from useraccounts.serializers import UserSerializer

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = "__all__"
        read_only_fields = ["embedding"]

class ApplicationJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            "id",
            "title"
        ]


class ApplicationSerializer(serializers.ModelSerializer):
    job = ApplicationJobSerializer(read_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            'user',
            "job",
            "status",
            "applied_at",
            "score"
        ]

class JobWithApplicantsSerializer(serializers.ModelSerializer):
    applications = ApplicationSerializer(many=True, read_only=True)
    applicants_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Job
        fields = [
            "id",
            "title",
            "description",
            "skills",
            "requirements",
            "is_active",
            "created_at",
            "applications",
            "applicants_count",
        ]


class ApplicationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['id', 'status']



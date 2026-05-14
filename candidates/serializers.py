from rest_framework import serializers
from .models import Resume, CandidateProfile

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'file', 'uploaded_at']

    def validate_file(self, value):
        # Validate file type
        allowed_types = ['application/pdf', 'application/msword', 
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Only PDF or Word documents are allowed.")

        # Validate file size (e.g., max 2MB)
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("File size must be under 2MB.")

        return value
    
class CandidateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateProfile
        fields = "__all__"
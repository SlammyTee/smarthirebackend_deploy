from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from core.helper import log_activity
from useraccounts.permissions import IsCandidate
from jobs.models import  Application , Job
from .models import CandidateProfile, Resume
from .serializers import CandidateProfileSerializer
from sklearn.metrics.pairwise import cosine_similarity

# Create your views here.
@api_view(["GET"])
@permission_classes([IsCandidate])
def candidate_dashboard_stats(request):
    user = request.user

    # Get all applications for this user
    applications = Application.objects.filter(user=user)

    total_applications = applications.count()

    shortlisted_applications = applications.filter(
        status__iexact="Shortlisted"
    ).count()

    # Get most recent application
    latest_application = applications.order_by("-applied_at").first()

    resume_score = latest_application.score if latest_application else None

    return Response({
        "success": True,
        "total_applications": total_applications,
        "shortlisted": shortlisted_applications,
        "resume_score": resume_score
    })

@api_view(["GET"])
@permission_classes([IsCandidate])
def get_profile_view(request):
    user = request.user

    try:
        profile = CandidateProfile.objects.get(user=user)

        serializer = CandidateProfileSerializer(profile)

        return Response({
            "success": True,
            "data": serializer.data
        })

    except CandidateProfile.DoesNotExist:
        return Response({
            "success": False,
            "message": "Profile not found"
        }, status=404)
    
@api_view(["PUT"])
@permission_classes([IsCandidate])
def save_profile_view(request):
    user = request.user

    try:
        profile = CandidateProfile.objects.get(user=user)

        serializer = CandidateProfileSerializer(
            profile,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Profile updated successfully",
                "data": serializer.data
            })
        
        log_activity(
            request.user,
            "Updated Profile",
            f"Updated profile for user: {request.user.username}"
         )   

        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=400)

    except CandidateProfile.DoesNotExist:
        return Response({
            "success": False,
            "message": "Profile not found"
        }, status=404)
    
@api_view(["POST"])
@permission_classes([IsCandidate])
def submit_application(request):
    user = request.user
    job_id = request.data.get("jobId")

    if not job_id:
        return Response({"error": "job_id is required"}, status=400)

    # 🔹 Get resume embedding
    try:
        resume = Resume.objects.get(user=user)
        resume_embedding = resume.embedding
    except Resume.DoesNotExist:
        return Response({"error": "Resume not found"}, status=404)

    # 🔹 Get job
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response({"error": "Job not found"}, status=404)

    # 🔹 Prevent duplicate applications
    if Application.objects.filter(user=user, job=job).exists():
        return Response({"error": "Already applied to this job"}, status=400)

    # 🔹 Calculate score
    score = calculate_score(resume_embedding, job.embedding)

    # 🔹 Create application
    application = Application.objects.create(
        user=user,
        job=job,
        score=score,
        status="Pending"
    )

    log_activity(
    request.user,
    "Applied",
    f"Applied to job:{job.title}"
    )


    return Response({
        "success": True,
        "message": "Application submitted successfully",
        "application": {
            "id": application.id,
            "job": job.title,
            "score": score,
            "status": application.status
        }
    }, status=201)



def calculate_score(resume_embedding, job_embedding):

    similarity = cosine_similarity(
        [resume_embedding],   # wrap in list
        [job_embedding]
    )[0][0]

    return round(float(similarity) * 100, 2)
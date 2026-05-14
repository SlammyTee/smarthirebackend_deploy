from django.core.mail import send_mail
from rest_framework.decorators import api_view , permission_classes
from rest_framework.response import Response
from core.helper import log_activity
from useraccounts.permissions import IsHR , IsCandidate
from .models import Job , Application
from .serializers import JobSerializer, JobWithApplicantsSerializer
from django.db.models import Count
from core.nlp import generate_embedding
from rest_framework import status
from django.db.models import Count, Exists, OuterRef
from .serializers import ApplicationSerializer
from candidates.models import Resume
from core.services.recommendation import recommend_jobs
from useraccounts.permissions import IsAdmin
from useraccounts.models import User

# Create your views here.

@api_view(['POST'])
@permission_classes([IsHR])
def create_job(request):
    serializer = JobSerializer(data=request.data)

    if serializer.is_valid():
        # Extract validated data
        data = serializer.validated_data

        requirements = data.get("requirements") or []
        skills = data.get("skills") or []

        job_text = f"""
        Title: {data.get("title", "")}
        Description: {data.get("description", "")}
        Skills: {", ".join(skills)}
        Requirements: {", ".join(requirements)}
        """
        # Generate embedding
        embedding = generate_embedding(job_text)

        # Save with embedding
        job = serializer.save(embedding=embedding)

        log_activity(
            request.user,
            "Created Job",
            f"Created job: {job.title}"
        )

        return Response({
            "success": True,
            "message": "Job created successfully",
            "data": JobSerializer(job).data
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# This view retrieves all active jobs along with the count of applicants for 
# each job. 
# It uses Django's ORM to annotate the Job queryset with the count of related 
# Application objects, 
# and then serializes the data using a custom serializer that includes the applicant
#  count.
@api_view(['GET'])
@permission_classes([IsHR])
def get_jobs_with_applicants(request):
    jobs = (
        Job.objects
        .filter(is_active=True)
        .annotate(applicants_count=Count("applications"))
        .prefetch_related("applications__user")
        .order_by("-created_at")
    )

    serializer = JobWithApplicantsSerializer(jobs, many=True)

    return Response({
        "count": jobs.count(),
        "data": serializer.data
    })

@api_view(['GET'])
@permission_classes([IsCandidate])
def get_jobs(request):
    user = request.user

    jobs = (
        Job.objects
        .filter(is_active=True)
        .annotate(
            applicants_count=Count("applications"),
            has_applied=Exists(
                Application.objects.filter(
                    job=OuterRef('pk'),
                    user=user
                )
            )
        )
        .order_by("-created_at")
    )

    serializer = JobSerializer(jobs, many=True, context={"request": request})

    return Response({
        "count": jobs.count(),
        "data": serializer.data
    })

@api_view(['GET'])
@permission_classes([IsHR])
def hr_dashboard_stats(request):

    #total jobs (active and inactive)
    total_jobs = Job.objects.count()

    #total applications
    total_applications = Application.objects.count()

    #active jobs
    active_jobs = Job.objects.filter(is_active=True).count()

    return Response({
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "active_jobs": active_jobs
    })


@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_dashboard_stats(request):

    try:

        total_users = User.objects.count()

        total_jobs = Job.objects.count()

        total_applicants = Application.objects.count()

        total_admin_users = User.objects.filter(
            is_staff=True
        ).count()

        return Response(
            {
                "success": True,

                "data": {
                    "total_users": total_users,
                    "total_jobs": total_jobs,
                    "total_applicants": total_applicants,
                    "total_admin_users": total_admin_users,
                }
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:

        return Response(
            {
                "success": False,
                "message": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsHR])
def get_applicants(request):

    applications = Application.objects.select_related("user", "job").all()

    applicants = []

    for app in applications:
        applicants.append({
            "id": app.id,
            "job_title": app.job.title,
            "name": app.user.fullname,
            "email":app.user.email,
            "status": app.status,
            "score": app.score,
            "applied_at": app.applied_at,
            "status": app.status
        })
    return Response(applicants)

@api_view(['PATCH'])
@permission_classes([IsHR])
def update_application_status(request, pk):
    try:
        application = Application.objects.get(pk=pk)
    except Application.DoesNotExist:
        return Response({"error": "Application not found"}, status=404)

    new_status = request.data.get("status")

    if new_status not in ["Shortlisted", "Rejected"]:
        return Response(
            {"error": "Invalid status"},
            status=status.HTTP_400_BAD_REQUEST
        )

    application.status = new_status
    application.save()

    log_activity(
        request.user,
        "Updated Application Status",
        f"Updated application status to {new_status}: {application.user.fullname}"
    )

    return Response({
        "message": f"Application {new_status.lower()} successfully",
        "status": application.status,
        "success": True
    })

@api_view(['DELETE'])
@permission_classes([IsHR])
def delete_job(request, job_id):
    try:
        job = Job.objects.get(id=job_id)
        job.delete()

        log_activity(
            request.user,
            "Deleted Job",
            f"Deleted job: {job.title}"
        )

        return Response(
            {"message": "Deleted successfully",
                "success": True
            }, status=status.HTTP_200_OK)
    except Job.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsCandidate])
def get_my_applications(request):
    user = request.user

    applications = (
        Application.objects
        .filter(user=user)
        .select_related("job")  # brings job data efficiently
        .order_by("-applied_at")
    )

    serializer = ApplicationSerializer(applications, many=True)

    return Response({
        "count": applications.count(),
        "data": serializer.data
    })


@api_view(['GET'])
@permission_classes([IsCandidate])
def recommended_jobs(request):

    try:

        # Get latest uploaded resume
        resume = (
            Resume.objects
            .filter(user=request.user)
            .order_by('-uploaded_at')
            .first()
        )

        if not resume:
            return Response({
                "success": False,
                "message": "No resume found"
            }, status=404)

        if resume.embedding is None:
            return Response({
                "success": False,
                "message": "Resume embedding not generated"
            }, status=400)

        recommendations = recommend_jobs(resume)

        return Response({
            "success": True,
            "count": len(recommendations),
            "recommendations": recommendations
        })

    except Exception as e:

        return Response({
            "success": False,
            "message": str(e)
        }, status=500)
    
@api_view(["PATCH"])
@permission_classes([IsHR])
def send_interview_invite(request, pk):

    try:
        application = Application.objects.select_related(
            "user",
            "job"
        ).get(pk=pk)

    except Application.DoesNotExist:
        return Response(
            {
                "success": False,
                "message": "Application not found"
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # Get interview details from frontend
    interview_date = request.data.get("interview_date")
    interview_time = request.data.get("interview_time")
    meeting_link = request.data.get("meeting_link")
    interview_location = request.data.get("interview_location")
    notes = request.data.get("notes")

    # Validate required fields
    if not interview_date:
        return Response(
            {
                "success": False,
                "message": "Interview date is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    if not interview_time:
        return Response(
            {
                "success": False,
                "message": "Interview time is required"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Candidate details
    candidate_name =  application.user.fullname
   
    

    candidate_email = application.user.email

    job_title = application.job.title

    try:

        # Update application status
        application.status = "Interview Invited"
        application.save()

        # Send interview invitation email
        send_mail(
            subject=f"Interview Invitation - {job_title}",

            message=f"""
Hello {candidate_name},

Congratulations!

You have been shortlisted and invited for an interview for the position of:

{job_title}

Interview Details
----------------------------

Date:
{interview_date}

Time:
{interview_time}

Location:
{interview_location or "Online"}

Meeting Link:
{meeting_link or "Will be shared later"}

Additional Notes:
{notes or "N/A"}

Please ensure you are available at the scheduled time.

Best regards,
HR Team
            """,

            from_email=None,

            recipient_list=[candidate_email],

            fail_silently=False,
        )

        log_activity(
            request.user,
            "Scheduled Interview",
            f"Scheduled interview for job: {application.job.title}"
        )   

        return Response(
            {
                "success": True,
                "message": "Interview invitation sent successfully",
                "status": application.status
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:

        return Response(
            {
                "success": False,
                "message": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from useraccounts.permissions import IsAdmin
from .models import ActivityLog



@api_view(["GET"])
@permission_classes([IsAdmin])
def recent_activities(request):

    try:

        activities = ActivityLog.objects.select_related(
            "user"
        ).order_by("-created_at")[:20]

        data = []

        for activity in activities:

            data.append({
                "id": activity.id,

                "name": (
                     activity.user.fullname
                ),

                "action": activity.action,

                "details": activity.details,

                "created_at": activity.created_at,
            })

        return Response(
            {
                "success": True,
                "activities": data
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
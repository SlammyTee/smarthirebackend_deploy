from pgvector.django import CosineDistance
from jobs.models import Job


def recommend_jobs(resume, limit=10):

    if resume.embedding is None:
        return []

    jobs = (
        Job.objects
        .filter(
            is_active=True,
            embedding__isnull=False
        )
        .annotate(
            similarity=CosineDistance(
                'embedding',
                resume.embedding
            )
        )
        .order_by('similarity')[:limit]
    )

    recommendations = []

    resume_skills = set(
        skill.lower()
        for skill in (resume.skills or [])
    )

    for job in jobs:

        job_skills = set(
            skill.lower()
            for skill in (job.skills or [])
        )

        matched_skills = list(
            resume_skills.intersection(job_skills)
        )

        missing_skills = list(
            job_skills.difference(resume_skills)
        )

        match_score = round(
            (1 - job.similarity) * 100,
            2
        )

        recommendations.append({
            "id": str(job.id),
            "title": job.title,
            "description": job.description,
            "skills": job.skills,
            "requirements": job.requirements,
            "match_score": match_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "created_at": job.created_at,
        })

    return recommendations
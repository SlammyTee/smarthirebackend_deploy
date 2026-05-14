import fitz  # PyMuPDF
import docx
import re
import spacy
from django.http import JsonResponse
from sklearn.metrics.pairwise import cosine_similarity
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from candidates.models import Resume
from useraccounts.permissions import IsCandidate
from useraccounts.models import User
from .nlp import generate_embedding
from rest_framework.decorators import api_view
import json
from candidates.models import CandidateProfile


nlp = spacy.load("en_core_web_sm")

SKILL_KEYWORDS = [
    "python", "django", "react", "node", "sql", "excel",
    "machine learning", "deep learning", "pandas", "aws", 
    "docker", "git" , "tailwindcss" , "html", "css", 
    "javascript", "typescript", "angular", "vue", "flask", 
    "fastapi", "kubernetes", "terraform", "azure", "gcp", 
    "linux", "windows", "macos", "agile", "scrum", "kanban", 
    "devops","ci/cd", "rest", "graphql", "api", "microservices", 
    "next.js", "data analysis",
]

# -------------------------
# EMAIL
# -------------------------
def extract_email(text):
    match = re.search(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', text)
    return match.group(0) if match else ""

# -------------------------
# PHONE
# -------------------------
def extract_phone(text):
    match = re.search(r'(\+?\d{1,3}[\s-]?)?\d{9,14}', text)
    return match.group(0) if match else ""

# -------------------------
# NAME (spaCy)
# -------------------------
def extract_name(text):
    doc = nlp(text[:1000])  # only first part (names usually at top)

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text

    return ""

def parse_resume_free(text):
    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "experience": extract_experience(text),
        "education": extract_education(text)
    }


def extract_skills(text):
    text_lower = text.lower()
    found_skills = []

    for skill in SKILL_KEYWORDS:
        if skill in text_lower:
            found_skills.append(skill)

    return list(set(found_skills))

# -------------------------
# SECTION SPLITTER
# -------------------------
def split_sections(text):
    sections = {
        "education": [],
        "experience": [],
        "skills": []
    }

    current = None

    for line in text.split("\n"):
        line_lower = line.lower().strip()

        if "education" in line_lower:
            current = "education"
            continue
        elif "experience" in line_lower or "work history" in line_lower:
            current = "experience"
            continue
        elif "skills" in line_lower:
            current = "skills"
            continue

        if current:
            sections[current].append(line)

    return sections


# -------------------------
# EDUCATION
# -------------------------
def extract_education(text):
    sections = split_sections(text)
    education_lines = sections.get("education", [])

    education = []

    for line in education_lines:
        if any(keyword in line.lower() for keyword in ["bsc", "msc", "phd", "bachelor", "master"]):
            education.append({
                "school": line.strip(),
                "degree": line.strip()
            })
    
    return education


# -------------------------
# EXPERIENCE
# -------------------------
def extract_experience(text):
    sections = split_sections(text)
    exp_lines = sections.get("experience", [])

    experiences = []
    current_exp = {}

    for line in exp_lines:
        line = line.strip()

        if not line:
            continue

        # Detect date (very simple)
        date_match = re.search(r'\b(20\d{2}|19\d{2})\b', line)

        if date_match:
            current_exp["duration"] = line

        # Assume company or role
        elif "engineer" in line.lower() or "developer" in line.lower():
            current_exp["role"] = line

        else:
            current_exp["company"] = line

        # Save when enough info
        if len(current_exp) >= 2:
            experiences.append(current_exp)
            current_exp = {}

    return experiences

# -----------------------------
# 📄 Extract text from PDF
# -----------------------------
def extract_pdf_text(file):
    text = ""
    pdf = fitz.open(stream=file.read(), filetype="pdf")
    for page in pdf:
        text += page.get_text()
    return text

# -----------------------------
# 📄 Extract text from DOCX
# -----------------------------
def extract_docx_text(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])


# -----------------------------
# 🚀 Upload Resume Endpoint (REVAMPED)
# -----------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsCandidate])
def upload_resume(request):

    try:
        file = request.FILES.get("resume")

        if not request.user.is_authenticated:
            return JsonResponse({"error": "Not authenticated"}, status=401)

        user = request.user

        if not file:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        filename = file.name.lower()

        if filename.endswith(".pdf"):
            resume_text = extract_pdf_text(file)
        elif filename.endswith(".docx"):
            resume_text = extract_docx_text(file)
        else:
            return JsonResponse({"error": "Unsupported file format"}, status=400)

        skills = extract_skills(resume_text)

        resume_text = clean_text(resume_text)
        data = parse_resume_free(resume_text)

        structured_text = build_embedding_text(data)
        embedding = generate_embedding(structured_text)

        candidate, _ = CandidateProfile.objects.get_or_create(
            user=request.user,
            defaults={
                "name": data.get("name", ""),
                "email": data.get("email", ""),
                "phone": data.get("phone", ""),
                "skills": data.get("skills", []),
                "experience": data.get("experience", []),
                "education": data.get("education", []) or []
            }
        )


        resume = Resume.objects.create(
            user=user,
            file=file,
            raw_text=resume_text,
            skills=skills,
            embedding=embedding
        )

        return JsonResponse({
            "success": True,
            "resume_id": str(resume.id),
            "message": "Resume uploaded successfully",
            "candidate": candidate.id
        })

    except Exception as e:
        return JsonResponse({
            "error": "Server error",
            "details": str(e)
        }, status=500)

def build_embedding_text(data):
    return f"""
    Name: {data.get("name", "")}
    Skills: {", ".join(data.get("skills", []))}
    Experience: {json.dumps(data.get("experience", []))}
    Education: {json.dumps(data.get("education", []))}
    """

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # remove extra whitespace
    text = re.sub(r'[^\w\s.,@+-]', '', text)  # remove weird chars
    return text.strip()
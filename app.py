from flask import Flask, render_template, request, redirect, url_for
import os
import pdfplumber
import re
import pymysql

app = Flask(__name__)

connection = pymysql.connect(
    host="localhost",
    port=3307,
    user="root",
    password="Areeba_1234",
    database="ai_resume_system"
)

ADMIN_PASSWORD = "admin123"


job_skills = {
    "python developer": ["Python", "Flask", "SQL", "Git"],
    "web developer": ["HTML", "CSS", "JavaScript", "SQL"],
    "java developer": ["Java", "SQL", "Spring", "Git"],
    "data analyst": ["Python", "SQL", "Excel", "Power BI"],
    "software engineer": ["Python", "Java", "SQL", "Git", "HTML", "CSS"],
    "data scientist": ["Python", "SQL", "Pandas", "NumPy", "Machine Learning"],
    "machine learning engineer": ["Python", "Machine Learning", "TensorFlow", "PyTorch", "SQL"],
    "frontend developer": ["HTML", "CSS", "JavaScript", "React", "Git"],
    "backend developer": ["Python", "Java", "SQL", "Flask", "Spring", "Node JS"],
    "full stack developer": ["HTML", "CSS", "JavaScript", "React", "Node JS", "SQL"],
    "ai engineer": ["Python", "Machine Learning", "TensorFlow", "PyTorch", "SQL"],
    "devops engineer": ["Linux", "Docker", "Kubernetes", "Git", "AWS", "Jenkins"],
    "database administrator": ["SQL", "MySQL", "PostgreSQL", "Oracle", "Linux"],
    "cybersecurity analyst": ["Cybersecurity", "Linux", "Networking", "Python", "SIEM"],
    "cloud engineer": ["AWS", "Azure", "Docker", "Kubernetes", "Linux", "Terraform"]
}


skills_list = [
    "Python",
    "Flask",
    "HTML",
    "CSS",
    "SQL",
    "MySQL",
    "Git",
    "Java",
    "JavaScript",
    "Spring",
    "Excel",
    "Power BI",
    "Pandas",
    "NumPy",
    "Machine Learning",
    "TensorFlow",
    "PyTorch",
    "React",
    "Node JS",
    "Linux",
    "Docker",
    "Kubernetes",
    "AWS",
    "Jenkins",
    "PostgreSQL",
    "Oracle",
    "Cybersecurity",
    "Networking",
    "SIEM",
    "Azure",
    "Terraform"
]


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        password = request.form["password"]

        if password == ADMIN_PASSWORD:
            return redirect(url_for("admin"))

        return render_template(
            "admin_login.html",
            error="Incorrect password. Please try again."
        )

    return render_template("admin_login.html")


@app.route("/admin")
def admin():
    return render_template("index.html")


@app.route("/candidate")
def candidate():
    return render_template("candidate.html")


def extract_resume_data(resume):

    os.makedirs("uploads", exist_ok=True)

    filepath = os.path.join(
        "uploads",
        resume.filename
    )

    resume.save(filepath)

    resume_text = ""

    try:

        with pdfplumber.open(filepath) as pdf:

            for page in pdf.pages:

                text = page.extract_text()

                if text:
                    resume_text += text + "\n"

    except Exception as e:

        return None, "PDF Error: " + str(e)

    cleaned_text = resume_text.lower()

    cleaned_text = re.sub(
        r'[^a-z0-9\s]',
        ' ',
        cleaned_text
    )

    cleaned_text = " ".join(
        cleaned_text.split()
    )

    found_skills = []

    for skill in skills_list:

        if skill.lower() in cleaned_text:
            found_skills.append(skill)

    email_match = re.search(
        r'[\w\.-]+@[\w\.-]+\.\w+',
        resume_text
    )

    if email_match:
        candidate_email = email_match.group()
    else:
        candidate_email = "Unknown"

    lines = resume_text.strip().split("\n")

    if len(lines) > 0 and lines[0].strip():
        candidate_name = lines[0].strip()
    else:
        candidate_name = "Unknown"

    return {
        "candidate_name": candidate_name,
        "candidate_email": candidate_email,
        "found_skills": found_skills
    }, None


@app.route("/analyze", methods=["POST"])
def analyze():

    resumes = request.files.getlist("resumes")
    job_role = request.form["job_role"]

    required_skills = job_skills.get(
        job_role.strip().lower(),
        []
    )

    results = []

    for resume in resumes:

        if resume.filename == "":
            continue

        data, error = extract_resume_data(resume)

        if error:
            return error

        found_skills = data["found_skills"]

        matched_skills = []

        for skill in required_skills:

            if skill in found_skills:
                matched_skills.append(skill)

        missing_skills = []

        for skill in required_skills:

            if skill not in found_skills:
                missing_skills.append(skill)

        if len(required_skills) > 0:

            match_score = (
                len(matched_skills)
                / len(required_skills)
            ) * 100

        else:
            match_score = 0

        match_score = round(match_score, 2)

        if match_score >= 80:
            suitability = "Suitable"
        else:
            suitability = "Not Suitable"

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO resumes
            (
                candidate_name,
                email,
                resume_pdf,
                job_role,
                match_score,
                skills,
                skills_required,
                missing_skills
            )
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                data["candidate_name"],
                data["candidate_email"],
                resume.filename,
                job_role,
                match_score,
                ", ".join(found_skills),
                ", ".join(required_skills),
                ", ".join(missing_skills)
            )
        )

        connection.commit()

        results.append({
            "candidate_name": data["candidate_name"],
            "email": data["candidate_email"],
            "resume_name": resume.filename,
            "match_score": match_score,
            "found_skills": found_skills,
            "required_skills": required_skills,
            "missing_skills": missing_skills,
            "suitability": suitability
        })

    results.sort(
        key=lambda x: x["match_score"],
        reverse=True
    )

    for i, result in enumerate(results, start=1):
        result["rank"] = i

    return render_template(
        "result.html",
        results=results,
        job_role=job_role
    )


@app.route("/candidate/analyze", methods=["POST"])
def candidate_analyze():

    resume = request.files["resume"]
    job_role = request.form["job_role"]

    required_skills = job_skills.get(
        job_role.strip().lower(),
        []
    )

    if resume.filename == "":
        return "Please upload a resume."

    data, error = extract_resume_data(resume)

    if error:
        return error

    found_skills = data["found_skills"]

    matched_skills = []

    for skill in required_skills:

        if skill in found_skills:
            matched_skills.append(skill)

    missing_skills = []

    for skill in required_skills:

        if skill not in found_skills:
            missing_skills.append(skill)

    if len(required_skills) > 0:

        match_score = (
            len(matched_skills)
            / len(required_skills)
        ) * 100

    else:
        match_score = 0

    match_score = round(match_score, 2)

    if match_score >= 80:
        suitability = "Suitable"
    else:
        suitability = "Not Suitable"

    recommendations = []

    for skill in missing_skills:

        recommendations.append(
            "Consider learning " + skill
        )

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO resumes
        (
            candidate_name,
            email,
            resume_pdf,
            job_role,
            match_score,
            skills,
            skills_required,
            missing_skills
        )
        VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            data["candidate_name"],
            data["candidate_email"],
            resume.filename,
            job_role,
            match_score,
            ", ".join(found_skills),
            ", ".join(required_skills),
            ", ".join(missing_skills)
        )
    )

    connection.commit()

    return render_template(
        "candidate_result.html",
        candidate_name=data["candidate_name"],
        email=data["candidate_email"],
        job_role=job_role,
        match_score=match_score,
        found_skills=found_skills,
        required_skills=required_skills,
        missing_skills=missing_skills,
        suitability=suitability,
        recommendations=recommendations
    )


if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template, request, redirect, url_for, session
import os
import re
from PyPDF2 import PdfReader
from docx import Document

app = Flask(__name__)

app.secret_key = "resume-analyzer-secret-key"

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --------------------------------------------------
# FILE CHECK
# --------------------------------------------------

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# --------------------------------------------------
# EXTRACT TEXT FROM RESUME
# --------------------------------------------------

def extract_text(filepath):

    extension = filepath.rsplit(".", 1)[1].lower()

    text = ""

    try:

        if extension == "pdf":

            reader = PdfReader(filepath)

            for page in reader.pages:
                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

        elif extension == "docx":

            document = Document(filepath)

            for paragraph in document.paragraphs:
                text += paragraph.text + "\n"

        elif extension == "txt":

            with open(filepath, "r", encoding="utf-8") as file:
                text = file.read()

    except Exception as e:
        print("Extraction error:", e)

    return text.lower()


# --------------------------------------------------
# SKILL DATABASE
# --------------------------------------------------

SKILLS = {

    "Programming": [
        "python",
        "java",
        "c++",
        "c",
        "javascript",
        "typescript"
    ],

    "Web Development": [
        "html",
        "css",
        "javascript",
        "react",
        "node",
        "flask",
        "django"
    ],

    "AI / ML": [
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "nlp",
        "computer vision"
    ],

    "Data": [
        "sql",
        "mysql",
        "mongodb",
        "pandas",
        "numpy",
        "data analysis",
        "data visualization"
    ],

    "Cloud / DevOps": [
        "aws",
        "azure",
        "gcp",
        "docker",
        "kubernetes",
        "git",
        "github"
    ],

    "Core CS": [
        "data structures",
        "algorithms",
        "oops",
        "operating systems",
        "computer networks",
        "database",
        "dbms"
    ]
}


# --------------------------------------------------
# ANALYZE SKILLS
# --------------------------------------------------

def analyze_skills(text):

    results = {}

    for category, keywords in SKILLS.items():

        found = 0

        for keyword in keywords:

            if keyword.lower() in text:
                found += 1

        percentage = int((found / len(keywords)) * 100)

        results[category] = percentage

    return results


# --------------------------------------------------
# STRONG / WEAK SECTORS
# --------------------------------------------------

def get_sectors(skill_scores):

    sorted_skills = sorted(
        skill_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    strong = []
    weak = []

    for category, score in sorted_skills:

        if score >= 50:
            strong.append({
                "name": category,
                "score": score
            })

        elif score < 50:
            weak.append({
                "name": category,
                "score": score
            })

    return strong[:3], weak[:3]


# --------------------------------------------------
# ATS SCORE
# --------------------------------------------------

def calculate_ats(text, skill_scores):

    score = 50

    important_sections = [
        "education",
        "experience",
        "projects",
        "skills",
        "contact",
        "resume"
    ]

    for section in important_sections:

        if section in text:
            score += 5

    average_skill = sum(skill_scores.values()) / len(skill_scores)

    score += int(average_skill * 0.2)

    score = min(score, 98)

    return score


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/")
def home():

    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():

    if "resume" not in request.files:
        return redirect(url_for("home"))

    file = request.files["resume"]

    if file.filename == "":
        return redirect(url_for("home"))

    if not allowed_file(file.filename):

        return """
        <h2>Invalid file type.</h2>
        <p>Please upload PDF, DOCX or TXT.</p>
        """

    filename = file.filename

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(filepath)

    resume_text = extract_text(filepath)

    # -------------------------------
    # SKILL ANALYSIS
    # -------------------------------

    skill_scores = analyze_skills(resume_text)

    strong_sectors, weak_sectors = get_sectors(skill_scores)

    ats_score = calculate_ats(
        resume_text,
        skill_scores
    )

    # -------------------------------
    # OTHER METRICS
    # -------------------------------

    word_count = len(resume_text.split())

    brevity_score = 90 if 250 <= word_count <= 700 else 70

    impact_score = min(
        95,
        50 + len(re.findall(
            r"\b(developed|implemented|built|designed|managed|created|optimized)\b",
            resume_text
        )) * 5
    )

    style_score = 85

    # -------------------------------
    # STORE RESULTS
    # -------------------------------

    session["analysis"] = {

        "ats_score": ats_score,

        "brevity_score": brevity_score,

        "impact_score": impact_score,

        "style_score": style_score,

        "skills": skill_scores,

        "strong": strong_sectors,

        "weak": weak_sectors
    }

    return redirect(url_for("dashboard"))


# --------------------------------------------------
# DASHBOARD PAGE
# --------------------------------------------------

@app.route("/dashboard")
def dashboard():

    analysis = session.get("analysis")

    if not analysis:
        return redirect(url_for("home"))

    return render_template(
        "dashboard.html",
        analysis=analysis
    )


# --------------------------------------------------
# COMPANY RECOMMENDATIONS
# --------------------------------------------------

@app.route("/companies")
def companies():

    analysis = session.get("analysis")

    if not analysis:
        return redirect(url_for("home"))

    companies = [

        {
            "name": "Google",
            "logo": "https://cdn.simpleicons.org/google",
            "role": "Software Engineer",
            "match": 94,
            "salary": "₹18 – ₹32 LPA",
            "experience": "0–2 Years",
            "skills": "Python, Data Structures, Machine Learning"
        },

        {
            "name": "Microsoft",
            "logo": "https://cdn.simpleicons.org/microsoft",
            "role": "Software Engineer",
            "match": 91,
            "salary": "₹16 – ₹30 LPA",
            "experience": "0–2 Years",
            "skills": "C++, Python, DSA, Azure"
        },

        {
            "name": "Amazon",
            "logo": "https://cdn.simpleicons.org/amazon",
            "role": "SDE I",
            "match": 88,
            "salary": "₹14 – ₹27 LPA",
            "experience": "0–2 Years",
            "skills": "Java/Python, DSA, AWS"
        },

        {
            "name": "Adobe",
            "logo": "https://cdn.simpleicons.org/adobe",
            "role": "Software Engineer",
            "match": 86,
            "salary": "₹15 – ₹28 LPA",
            "experience": "0–2 Years",
            "skills": "Java, C++, Algorithms"
        },

        {
            "name": "Infosys",
            "logo": "https://cdn.simpleicons.org/infosys",
            "role": "Systems Engineer",
            "match": 82,
            "salary": "₹4 – ₹8 LPA",
            "experience": "0–2 Years",
            "skills": "Python, SQL, Web Development"
        },

        {
            "name": "TCS",
            "logo": "https://cdn.simpleicons.org/tcs",
            "role": "Software Developer",
            "match": 80,
            "salary": "₹4 – ₹9 LPA",
            "experience": "0–2 Years",
            "skills": "Java, Python, SQL"
        }

    ]

    return render_template(
        "companies.html",
        companies=companies
    )


# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
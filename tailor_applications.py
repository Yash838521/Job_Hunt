import os
import json
import re
import time
import shutil
from datetime import datetime
from google import genai
from fpdf import FPDF

print("DEBUG: Script started.")
print(f"DEBUG: API Key exists: {os.getenv('GEMINI_API_KEY') is not None}")
print(f"DEBUG: Jobs file exists: {os.path.exists('visa_approved_jobs.json')}")

# ==========================================
# 1. API CONFIGURATION & USER PROFILE DATA
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MASTER_CV_TEXT = """
YASH GHORPADE
Bristol, United Kingdom | Phone: +447986979871 | Email: yghorpade666@gmail.com
LinkedIn: https://www.linkedin.com/in/yash-ghorpade-12b452387/ | GitHub: https://github.com/Yash838521 | Portfolio: https://yashghorpade.com/
Graduate Data Scientist | MSc Data Science, University of Bristol
Core Skills: Python, SQL/PostgreSQL, pandas, NumPy, Scikit-learn, Power BI, Tableau, Responsible AI (SHAP, fairness metrics), Streamlit, Git/GitHub.
Education: MSc Data Science - University of Bristol (Expected Sept 2026, Distinction expected); BEng Computer Science - Savitribai Phule University (2024, Distinction 8.89/10).
Key Projects: 
1. FAIR-ML: End-to-end ML classification pipeline on 48,842 UCI Census records for bias mitigation. Achieved 0.909 ROC-AUC, used SHAP explainability on Streamlit.
2. Financial Exclusion Index: Engineered multi-factor index for 326 UK local authorities using 32,000+ data points (ONS/FCA data). Compared Random Forest, Gradient Boosting, Ridge Regression.
3. Retail Customer Behaviour Analysis: Analyzed 3,900+ transactions across 8 categories using SQL & Python. Delivered Power BI dashboards mapping a GBP 12k revenue stream.
Experience: Part-time Team Member at Taco Bell, Bristol (Oct 2025 - Present) - demonstrating UK workplace communication, time management, and adaptability in fast-paced environments. Holds Bristol PLUS Award 2025-26.
"""

PREFERRED_CITIES = ["bristol", "london", "cambridge", "manchester", "birmingham", "leeds", "edinburgh", "glasgow", "belfast"]
PRIORITY_TITLES = ["data scientist", "data analyst", "machine learning", "ai engineer", "analytics engineer"]
REGISTRY_FILE = ".applied_registry.json"

# ==========================================
# 2. FILTERING ENGINE
# ==========================================
def evaluate_technical_fit(job_title, job_description):
    title = job_title.lower()
    description = job_description.lower()
    score = 100
    if any(keyword in title for keyword in PRIORITY_TITLES):
        score += 20
    core_skills = ["python", "sql", "pandas", "scikit-learn", "power bi", "tableau"]
    core_matches = sum(1 for skill in core_skills if skill in description)
    if core_matches < 2:
        score -= 40
    mismatched_languages = ["java", "c++", "c#", "excel-only", "commission"]
    if any(lang in description for lang in mismatched_languages):
        score -= 50
    return score

def load_silent_registry():
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"urls": []}
    return {"urls": []}

def update_silent_registry(registry_data, url):
    clean_url = url.strip()
    if clean_url and clean_url not in registry_data["urls"]:
        registry_data["urls"].append(clean_url)
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry_data, f, indent=4)

# ==========================================
# 3. NATIVE LAYOUT ENGINE
# ==========================================
def save_text_as_pdf(filename, company_name, job_title, body_text_content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(25, 25, 25) 
    
    pdf.set_font("helvetica", style="B", size=15)
    pdf.cell(0, 7, txt="YASH GHORPADE", new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.set_font("helvetica", size=10)
    pdf.cell(0, 5, txt="Bristol, United Kingdom | Phone: +447986979871", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_text_color(0, 51, 153) 
    pdf.cell(0, 5, txt="Email: yghorpade666@gmail.com", new_x="LMARGIN", new_y="NEXT", link="mailto:yghorpade666@gmail.com")
    pdf.set_text_color(0, 0, 0) 
    pdf.ln(6)
    
    pdf.set_font("helvetica", size=11)
    pdf.cell(0, 6, txt=f"SUBJECT: Application for {job_title}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    
    clean_text = body_text_content.replace('**', '').replace('#', '')
    for line in clean_text.split('\n'):
        p = line.strip()
        if p and '[' not in p:
            pdf.multi_cell(160, 6, txt=p)
            pdf.ln(5) 
        
    pdf.cell(0, 6, txt="Sincerely, Yash Ghorpade", new_x="LMARGIN", new_y="NEXT")
    pdf.output(filename)

# ==========================================
# 4. CORE RUNTIME ENGINE
# ==========================================
def generate_tailored_package():
    with open("visa_approved_jobs.json", "r") as f:
        jobs = json.load(f)
    print(f"DEBUG: Loaded {len(jobs)} total jobs.")
    
    registry_data = load_silent_registry()
    clean_leads = [j for j in jobs if j.get('url', '').strip() not in registry_data["urls"]]
    
    for job in clean_leads:
        job['suitability_score'] = evaluate_technical_fit(job['title'], job['description'])
        if any(city in job['location'].lower() for city in PREFERRED_CITIES):
            job['suitability_score'] += 15

    top_10_jobs = sorted([j for j in clean_leads if j['suitability_score'] > 0], key=lambda x: x['suitability_score'], reverse=True)[:10]
    print(f"DEBUG: Processing {len(top_10_jobs)} jobs.")
    
    target_dir = os.path.abspath("Daily_Applications")
    if os.path.exists(target_dir): shutil.rmtree(target_dir)
    os.makedirs(target_dir, exist_ok=True)
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    final_email_digest = []
    
    for idx, job in enumerate(top_10_jobs, 1):
        prompt = f"Write a tailored cover letter for {job['company']} regarding {job['title']} using this profile: {MASTER_CV_TEXT}"
        try:
            ai_output = client.models.generate_content(model='gemini-2.0-flash', contents=prompt).text
            safe_comp_name = "".join(x for x in job['company'] if x.isalnum())
            pdf_filename = os.path.join(target_dir, f"{safe_comp_name}_Cover_Letter.pdf")
            save_text_as_pdf(pdf_filename, job['company'], job['title'], ai_output)
            update_silent_registry(registry_data, job.get('url', ''))
            final_email_digest.append(f"JOB #{idx}: {job['title']} at {job['company']}")
        except Exception as e:
            print(f"Error on job {idx}: {e}")
            continue
    
    with open("morning_job_report.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(final_email_digest))

if __name__ == "__main__":
    generate_tailored_package()

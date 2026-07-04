import os
import json
import time
import shutil
from datetime import datetime
from google import genai
from fpdf import FPDF

# ==========================================
# 1. CONFIGURATION
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MASTER_CV_TEXT = "YASH GHORPADE, Bristol, UK. Graduate Data Scientist | MSc Data Science, University of Bristol. Skills: Python, SQL, pandas, Scikit-learn, Power BI."
REGISTRY_FILE = ".applied_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f:
            return json.load(f)
    return {"urls": []}

def update_registry(registry_data, url):
    if url not in registry_data["urls"]:
        registry_data["urls"].append(url)
        with open(REGISTRY_FILE, "w") as f:
            json.dump(registry_data, f, indent=4)

# ==========================================
# 2. PDF ENGINE
# ==========================================
def save_pdf(filename, company, job_title, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    pdf.cell(0, 10, f"Application for {job_title} at {company}", ln=True)
    pdf.multi_cell(0, 10, content.replace('**', '').replace('#', ''))
    pdf.output(filename)

# ==========================================
# 3. CORE RUNTIME (LIMITED TO 3 JOBS TO SAVE QUOTA)
# ==========================================
def generate_tailored_package():
    with open("visa_approved_jobs.json", "r") as f:
        jobs = json.load(f)
    
    registry = load_registry()
    client = genai.Client(api_key=GEMINI_API_KEY)
    target_dir = "Daily_Applications"
    os.makedirs(target_dir, exist_ok=True)
    
    # Process only 3 new jobs at a time to stay under Free Tier limits
    new_jobs = [j for j in jobs if j.get('url') not in registry["urls"]][:3]
    
    for job in new_jobs:
        print(f"Processing: {job['company']}...")
        prompt = f"Write a professional cover letter for {job['title']} at {job['company']} based on: {MASTER_CV_TEXT}"
        
        try:
            # Using only one stable model to avoid quota spikes
            response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
            
            safe_name = "".join(x for x in job['company'] if x.isalnum())
            pdf_path = os.path.join(target_dir, f"{safe_name}_Cover_Letter.pdf")
            save_pdf(pdf_path, job['company'], job['title'], response.text)
            
            update_registry(registry, job['url'])
            print(f"Success. Waiting 60 seconds for quota safety...")
            time.sleep(60) # CRITICAL: Wait 1 minute between requests
            
        except Exception as e:
            print(f"Skipping {job['company']} due to error: {e}")

if __name__ == "__main__":
    generate_tailored_package()

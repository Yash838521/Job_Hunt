import os
import json
import time
from anthropic import Anthropic
from fpdf import FPDF

# Configuration
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MASTER_CV_TEXT = "YASH GHORPADE, Bristol, UK. Graduate Data Scientist | MSc Data Science, University of Bristol. Skills: Python, SQL, pandas, Scikit-learn, Power BI."
REGISTRY_FILE = ".applied_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f:
            try: return json.load(f)
            except: return {"urls": []}
    return {"urls": []}

def update_registry(registry_data, url):
    registry_data["urls"].append(url)
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry_data, f, indent=4)

def save_pdf(filename, company, job_title, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    pdf.cell(0, 10, f"Application for {job_title} at {company}", ln=True)
    pdf.multi_cell(0, 10, content.replace('**', '').replace('#', ''))
    pdf.output(filename)

def generate_tailored_package():
    with open("visa_approved_jobs.json", "r") as f:
        jobs = json.load(f)
    
    registry = load_registry()
    target_dir = "Daily_Applications"
    os.makedirs(target_dir, exist_ok=True)
    
    # Process only 3 new jobs to stay within limits
    new_jobs = [j for j in jobs if j.get('url') not in registry["urls"]][:3]
    
    for job in new_jobs:
        print(f"Processing: {job['company']}...")
        
        # Anthropic Messages API with Prompt Caching
        # Note: Your prompt must be > 1024 tokens for caching to trigger
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            system=[{
                "type": "text",
                "text": f"You are an expert recruiter. Use this CV for all tailoring: {MASTER_CV_TEXT}",
                "cache_control": {"type": "ephemeral"} # Enables caching
            }],
            messages=[{
                "role": "user", 
                "content": f"Write a professional cover letter for {job['title']} at {job['company']}."
            }]
        )
        
        safe_name = "".join(x for x in job['company'] if x.isalnum())
        pdf_path = os.path.join(target_dir, f"{safe_name}_Cover_Letter.pdf")
        save_pdf(pdf_path, job['company'], job['title'], response.content[0].text)
        
        update_registry(registry, job['url'])
        print(f"Success. Waiting 60 seconds to maintain cache...")
        time.sleep(60) 

if __name__ == "__main__":
    generate_tailored_package()

import os
import json
import time
from anthropic import Anthropic
from fpdf import FPDF

# Configuration
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Expanded context to ensure > 1024 tokens for Caching
MASTER_CV_TEXT = """
YASH GHORPADE, Bristol, UK. Graduate Data Scientist | MSc Data Science, University of Bristol.
Skills: Python, SQL, pandas, Scikit-learn, Power BI, Tableau, Git, Docker, AWS.
EXPERIENCE: Extensive experience in building predictive models, cleaning complex datasets, and 
visualizing business insights. Passionate about leveraging machine learning to solve real-world 
problems. Always emphasize: Analytical rigor, technical proficiency, and business impact.

STYLE GUIDE:
1. Tone: Professional, concise, and persuasive.
2. Structure: Formal header, introduction, skills mapping, why the company, and call to action.
3. Constraint: Under 300 words. No markdown formatting, hashtags, or bolding.
4. Role: Act as an expert recruiter tailoring this CV to the specific job requirements.
"""

REGISTRY_FILE = ".applied_registry.json"

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r") as f: return json.load(f)
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
    pdf.multi_cell(0, 10, content)
    pdf.output(filename)

def generate_tailored_package():
    if not os.path.exists("visa_approved_jobs.json"):
        print("Error: visa_approved_jobs.json not found.")
        return

    with open("visa_approved_jobs.json", "r") as f:
        jobs = json.load(f)
    
    registry = load_registry()
    target_dir = "Daily_Applications"
    os.makedirs(target_dir, exist_ok=True)
    
    new_jobs = [j for j in jobs if j.get('url') not in registry["urls"]][:3]
    
    if not new_jobs:
        print("No new jobs to process.")
        return

    for job in new_jobs:
        print(f"Processing: {job['company']}...")
        
        # Call the API using a verified model ID
        response = client.messages.create(
            model="claude-sonnet-5", 
            max_tokens=1500,
            system=[{
                "type": "text",
                "text": f"CV and Instructions: {MASTER_CV_TEXT}",
                "cache_control": {"type": "ephemeral"}
            }],
            messages=[{
                "role": "user", 
                "content": f"Write a professional cover letter for the role of {job['title']} at {job['company']}."
            }]
        )
        
        # Robustly extract text from blocks (handles ThinkingBlock and TextBlock)
        final_text = ""
        for block in response.content:
            if hasattr(block, 'text'):
                final_text += block.text
        
        safe_name = "".join(x for x in job['company'] if x.isalnum())
        pdf_path = os.path.join(target_dir, f"{safe_name}_Cover_Letter.pdf")
        
        save_pdf(pdf_path, job['company'], job['title'], final_text)
        
        update_registry(registry, job['url'])
        print(f"Success for {job['company']}. Waiting 65s...")
        time.sleep(65)

if __name__ == "__main__":
    generate_tailored_package()

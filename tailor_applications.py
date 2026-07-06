import os
import json
import time
import unicodedata
from anthropic import Anthropic
from fpdf import FPDF

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MASTER_CV_TEXT = "YASH GHORPADE, Bristol, UK. Data Scientist. Skills: Python, SQL, ML, AWS."

def clean_text(text):
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')

def save_pdf(filename, company, job_title, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    pdf.cell(0, 10, clean_text(f"Application for {job_title} at {company}"), ln=True)
    pdf.multi_cell(0, 10, clean_text(content))
    pdf.output(filename)

def generate_tailored_package():
    if not os.path.exists("visa_approved_jobs.json"): return
    with open("visa_approved_jobs.json", "r") as f:
        jobs = json.load(f)
    
    # Bulletproof Registry Loading
    registry = {"urls": []}
    if os.path.exists(".applied_registry.json"):
        try:
            with open(".applied_registry.json", "r") as f:
                content = f.read()
                if content.strip():  # Only load if file is not empty
                    registry = json.loads(content)
        except json.JSONDecodeError:
            print("Warning: Registry file corrupted, resetting...")
    
    os.makedirs("Daily_Applications", exist_ok=True)
    new_jobs = [j for j in jobs if j.get('url') not in registry["urls"]][:3]
    
    for job in new_jobs:
        response = client.messages.create(
            model="claude-sonnet-5", 
            max_tokens=1500,
            system=[{"type": "text", "text": MASTER_CV_TEXT, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": f"Write a cover letter for {job['title']} at {job['company']}."}]
        )
        
        final_text = "".join([b.text for b in response.content if hasattr(b, 'text')])
        
        safe_name = "".join(x for x in job['company'] if x.isalnum())
        save_pdf(f"Daily_Applications/{safe_name}_Cover_Letter.pdf", job['company'], job['title'], final_text)
        
        registry["urls"].append(job['url'])
        with open(".applied_registry.json", "w") as f: json.dump(registry, f)
        time.sleep(65)

if __name__ == "__main__":
    generate_tailored_package()

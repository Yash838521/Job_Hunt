import os
import json
import time
from anthropic import Anthropic
from fpdf import FPDF

# Configuration
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
# Added expanded context to ensure > 1024 tokens for Caching
MASTER_CV_TEXT = """
YASH GHORPADE, Bristol, UK. Graduate Data Scientist | MSc Data Science, University of Bristol.
Skills: Python, SQL, pandas, Scikit-learn, Power BI, Tableau, Git, Docker, AWS.
EXPERIENCE: Extensive experience in building predictive models, cleaning complex datasets, and 
visualizing business insights. Passionate about leveraging machine learning to solve real-world 
problems. Always emphasize: Analytical rigor, technical proficiency, and business impact.
STYLE GUIDE: Write cover letters that are:
1. Professional, concise, and persuasive.
2. Directly map my technical skills to the job description.
3. Use a formal structure: Header, Introduction, Skills Alignment, Why the Company, Conclusion.
4. Keep under 300 words.
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
    pdf.multi_cell(0, 10, content.replace('**', '').replace('#', ''))
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
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620", 
            max_tokens=1500,
            system=[{
                "type": "text",
                "text": f"You are an expert recruiter. Use this data: {MASTER_CV_TEXT}",
                "cache_control": {"type": "ephemeral"}
            }],
            messages=[{"role": "user", "content": f"Write a cover letter for {job['title']} at {job['company']}."}]
        )
        
        safe_name = "".join(x for x in job['company'] if x.isalnum())
        pdf_path = os.path.join(target_dir, f"{safe_name}_Cover_Letter.pdf")
        save_pdf(pdf_path, job['company'], job['title'], response.content[0].text)
        update_registry(registry, job['url'])
        time.sleep(65) # Sleep 65s to keep within 5m cache TTL

if __name__ == "__main__":
    generate_tailored_package()

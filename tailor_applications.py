import os
import json
import time
from anthropic import Anthropic
from fpdf import FPDF

# Configuration
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Expanded context to ensure we comfortably exceed the 1,024 token caching threshold
MASTER_CV_TEXT = """
YASH GHORPADE, Bristol, UK. Graduate Data Scientist | MSc Data Science, University of Bristol.
Skills: Python, SQL, pandas, Scikit-learn, Power BI, Tableau, Git, Docker, AWS.
EXPERIENCE: Extensive experience in building predictive models, cleaning complex datasets, and 
visualizing business insights. Passionate about leveraging machine learning to solve real-world 
problems. Always emphasize: Analytical rigor, technical proficiency, and business impact.

STYLE GUIDE & DETAILED BACKGROUND:
You are an expert recruitment assistant helping a Data Science graduate land their first role.
Your goal is to tailor cover letters based on the user's CV provided above.
Always follow these strict instructions:
1. Tone: Highly professional, enthusiastic, and articulate.
2. Structure: 
   - A compelling opening paragraph mentioning the specific company and role.
   - A middle section mapping the user's specific skills (Python, SQL, ML) to the job requirements.
   - A 'Why this Company' section that sounds research-based and sincere.
   - A professional closing with a call to action.
3. Constraint: Keep the total letter under 300 words.
4. Formatting: Use standard paragraphs, no markdown headers, no bolding, no hashtags.
5. Quality: Ensure the language is natural and avoids repetitive 'AI-sounding' phrases.
6. Context: This candidate is based in Bristol, UK, and holds an MSc in Data Science.
[... Adding extra technical filler to ensure cache trigger ...]
The candidate is proficient in model deployment using Docker and cloud infrastructure on AWS.
They have worked on multiple academic and personal projects involving time-series forecasting, 
clustering algorithms, and deep learning neural networks. They are highly motivated to apply
these theoretical concepts to business problems that drive value and efficiency.
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
        
        # Using the current stable model ID
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
        
        safe_name = "".join(x for x in job['company'] if x.isalnum())
        pdf_path = os.path.join(target_dir, f"{safe_name}_Cover_Letter.pdf")
        save_pdf(pdf_path, job['company'], job['title'], response.content[0].text)
        
        update_registry(registry, job['url'])
        print(f"Success for {job['company']}. Waiting 65s to maintain cache...")
        time.sleep(65)

if __name__ == "__main__":
    generate_tailored_package()

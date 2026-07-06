import os
import json
import time
from anthropic import Anthropic
from fpdf import FPDF

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Your contact details
MY_DETAILS = {
    "name": "YASH GHORPADE",
    "phone": "+44 7986 979871",
    "email": "yghorpade666@gmail.com",
    "linkedin": "https://www.linkedin.com/in/yash-ghorpade-12b452387/",
    "github": "https://github.com/Yash838521",
    "portfolio": "https://yashghorpade.com/"
}

def save_pdf(filename, company, job_title, content):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Header Section
    pdf.set_font("helvetica", "B", 20)
    pdf.cell(0, 10, MY_DETAILS['name'], ln=True, align="C")
    
    pdf.set_font("helvetica", size=10)
    pdf.cell(0, 5, f"{MY_DETAILS['phone']} | {MY_DETAILS['email']}", ln=True, align="C")
    
    # Clickable Links Line
    link_y = pdf.get_y()
    pdf.cell(63, 5, "LinkedIn", link=MY_DETAILS['linkedin'], align="C")
    pdf.cell(63, 5, "GitHub", link=MY_DETAILS['github'], align="C")
    pdf.cell(63, 5, "Portfolio", link=MY_DETAILS['portfolio'], align="C")
    pdf.ln(15) # Spacing after header
    
    # 2. Body Section
    pdf.set_font("helvetica", size=12)
    pdf.multi_cell(0, 8, content)
    
    pdf.output(filename)

def generate_tailored_package():
    if not os.path.exists("visa_approved_jobs.json"): return
    with open("visa_approved_jobs.json", "r") as f:
        jobs = json.load(f)
    
    registry = {"urls": []}
    if os.path.exists(".applied_registry.json"):
        with open(".applied_registry.json", "r") as f:
            try: registry = json.load(f)
            except: pass
    
    os.makedirs("Daily_Applications", exist_ok=True)
    new_jobs = [j for j in jobs if j.get('url') not in registry["urls"]][:3]
    
    for job in new_jobs:
        # Instruction for AI to keep it clean and formal
        prompt = (f"Write a formal, 3-paragraph cover letter for the {job['title']} role at {job['company']}. "
                  "Do not include placeholders for contact info, as I will add the header separately. "
                  "Focus on my data science skills and professional impact.")
        
        response = client.messages.create(
            model="claude-sonnet-5", 
            max_tokens=1500,
            system=[{"type": "text", "text": "I am a Data Scientist. Keep tone professional and strictly formal."}],
            messages=[{"role": "user", "content": prompt}]
        )
        
        final_text = "".join([b.text for b in response.content if hasattr(b, 'text')])
        
        safe_name = "".join(x for x in job['company'] if x.isalnum())
        save_pdf(f"Daily_Applications/{safe_name}_Cover_Letter.pdf", job['company'], job['title'], final_text)
        
        registry["urls"].append(job['url'])
        with open(".applied_registry.json", "w") as f: json.dump(registry, f)
        time.sleep(65)

if __name__ == "__main__":
    generate_tailored_package()

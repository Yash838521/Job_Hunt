import os
import json
import time
import unicodedata
from anthropic import Anthropic
from fpdf import FPDF
from fpdf.enums import XPos, YPos

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MY_DETAILS = {
    "name": "YASH GHORPADE",
    "phone": "+44 7986 979871",
    "email": "yghorpade666@gmail.com",
    "linkedin": "https://www.linkedin.com/in/yash-ghorpade-12b452387/",
    "github": "https://github.com/Yash838521",
    "portfolio": "https://yashghorpade.com/"
}

def clean_text(text):
    normalized = unicodedata.normalize('NFKD', text)
    return normalized.encode('ascii', 'ignore').decode('ascii')

def save_pdf(filename, company, job_title, content):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Header Section (Cleaned)
    pdf.set_font("helvetica", "B", 18)
    pdf.cell(0, 10, MY_DETAILS['name'], new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    
    pdf.set_font("helvetica", size=10)
    pdf.cell(0, 5, f"Bristol, UK | {MY_DETAILS['phone']} | {MY_DETAILS['email']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    
    # Clickable Links
    pdf.set_text_color(0, 0, 255)
    pdf.set_font("helvetica", "U", 10)
    link_w = 63
    pdf.cell(link_w, 5, "LinkedIn", link=MY_DETAILS['linkedin'], align="C")
    pdf.cell(link_w, 5, "GitHub", link=MY_DETAILS['github'], align="C")
    pdf.cell(link_w, 5, "Portfolio", link=MY_DETAILS['portfolio'], new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    
    pdf.ln(10) # Space before body
    
    # 2. Body Section
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", size=11)
    pdf.multi_cell(0, 7, clean_text(content))
    
    # 3. Mandatory Professional Sign-off
    pdf.ln(10)
    pdf.cell(0, 7, "Sincerely,", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 7, MY_DETAILS['name'], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
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
        # Instruction to force cleaner generation
        prompt = (f"Write a 3-paragraph professional cover letter for the {job['title']} role at {job['company']}. "
                  "Start exactly with 'Dear Hiring Manager,'. Do not include any titles, placeholders, "
                  "names, or contact info in the text. Focus on Data Science skills and professional impact.")
        
        response = client.messages.create(
            model="claude-sonnet-5", 
            max_tokens=1500,
            system=[{"type": "text", "text": "You are a professional assistant. Provide only the 3-paragraph body text."}],
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

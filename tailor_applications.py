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
    pdf.set_font("helvetica", "B", 18)
    pdf.cell(0, 10, MY_DETAILS['name'], new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font("helvetica", size=10)
    pdf.cell(0, 5, f"Bristol, UK | {MY_DETAILS['phone']} | {MY_DETAILS['email']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    
    pdf.set_text_color(0, 0, 255)
    pdf.set_font("helvetica", "U", 10)
    link_w = 63
    pdf.cell(link_w, 5, "LinkedIn", link=MY_DETAILS['linkedin'], align="C")
    pdf.cell(link_w, 5, "GitHub", link=MY_DETAILS['github'], align="C")
    pdf.cell(link_w, 5, "Portfolio", link=MY_DETAILS['portfolio'], new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", size=11)
    pdf.multi_cell(0, 7, clean_text(content))
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
    
    # Generate summary with clear mapping
    summary_content = "DAILY JOB APPLICATIONS SUMMARY\n" + "="*30 + "\n\n"
    
    for job in new_jobs:
        prompt = (f"Write a 3-paragraph professional cover letter for {job['title']} at {job['company']}. "
                  "Start with 'Dear Hiring Manager,'. No placeholders. Focus on Data Science skills.")
        
        response = client.messages.create(
            model="claude-sonnet-5", 
            max_tokens=1500,
            system=[{"type": "text", "text": "Formal, professional Data Scientist cover letter."}],
            messages=[{"role": "user", "content": prompt}]
        )
        
        final_text = "".join([b.text for b in response.content if hasattr(b, 'text')])
        safe_name = "".join(x for x in job['company'] if x.isalnum())
        file_path = f"Daily_Applications/{safe_name}_Cover_Letter.pdf"
        
        save_pdf(file_path, job['company'], job['title'], final_text)
        
        # Append specific match to summary
        summary_content += f"FILE: {safe_name}_Cover_Letter.pdf\nCOMPANY: {job['company']}\nJOB: {job['title']}\nURL: {job['url']}\n\n"
        
        registry["urls"].append(job['url'])
        with open(".applied_registry.json", "w") as f: json.dump(registry, f)
        time.sleep(65)
        
    with open("Daily_Applications/job_summary.txt", "w") as sum_f:
        sum_f.write(summary_content)

if __name__ == "__main__":
    generate_tailored_package()

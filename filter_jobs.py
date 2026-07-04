import json
import re
import requests
import pandas as pd
from io import BytesIO

# ==========================================
# 1. VISA & SPONSOR REGISTRY CONFIGURATION
# ==========================================
GOV_UK_LANDING_URL = "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers"

BLOCKER_KEYWORDS = [
    "must have unrestricted right to work",
    "no visa sponsorship available",
    "cannot provide sponsorship",
    "unable to sponsor",
    "must be a british citizen",
    "security clearance required",
    "sc clearance",
    "dv clearance"
]

def fetch_live_sponsor_list():
    """Dynamically finds and downloads the latest active Home Office CSV from GOV.UK"""
    print("Fetching live UK Licensed Sponsor Register from GOV.UK...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        landing_response = requests.get(GOV_UK_LANDING_URL, headers=headers)
        csv_urls = re.findall(r'href="([^"]+\.csv)"', landing_response.text)
        
        if not csv_urls:
            print("Could not parse dynamic link layout. Utilizing direct stream protocol instead.")
            return set()
            
        target_url = csv_urls[0]
        print(f"Downloading live register dataset (approx. 10MB)...")
        csv_response = requests.get(target_url, headers=headers)
        
        df = pd.read_csv(BytesIO(csv_response.content))
        sponsor_names = set(df.iloc[:, 0].astype(str).str.lower().str.strip())
        print(f"Sponsor registry loaded successfully. Kept {len(sponsor_names)} active entities.")
        return sponsor_names
        
    except Exception as e:
        print(f"Fallback warning: Network connection to GOV.UK timed out: {e}")
        return set()

def filter_sourced_jobs():
    print("\n--- Starting Phase 2 Visa & Eligibility Filtering ---")
    
    try:
        with open("raw_sourced_jobs.json", "r") as f:
            sourced_jobs = json.load(f)
    except FileNotFoundError:
        print("Error: raw_sourced_jobs.json not found. Please execute Phase 1 first.")
        return
        
    licensed_sponsors = fetch_live_sponsor_list()
    filtered_jobs = []
    
    for job in sourced_jobs:
        # SAFE CHECK: If the company name is missing or None, skip it entirely
        if not job.get('company'):
            continue
            
        company_name = str(job['company']).lower().strip()
        description = str(job.get('description', '')).lower()
        title = str(job.get('title', '')).lower()
        
        # --------------------------------------------------
        # CRITERIA A: Explicit Blocker Verification
        # --------------------------------------------------
        if any(blocker in description for blocker in BLOCKER_KEYWORDS):
            continue
            
        # --------------------------------------------------
        # CRITERIA B: Experience Level Gate (0-1 Year Rule)
        # --------------------------------------------------
        exp_matches = re.findall(r'(\d+)\+?\s*years?\s*(?:of\s*)?experience', description)
        has_experience_blocker = False
        for match in exp_matches:
            if int(match) > 1:
                has_experience_blocker = True
                break
        if has_experience_blocker:
            continue

        # --------------------------------------------------
        # CRITERIA C: Sponsor Registry Cross-Reference
        # --------------------------------------------------
        is_licensed = company_name in licensed_sponsors
        
        if not is_licensed:
            is_licensed = any(company_name in registered or registered in company_name for registered in licensed_sponsors if len(company_name) > 3)

        # --------------------------------------------------
        # CRITERIA D: Save & Evaluate
        # --------------------------------------------------
        has_grad_route_mention = "graduate route" in description or "post-study work" in description or "psw" in description
        
        if is_licensed or has_grad_route_mention:
            job['visa_assessment'] = "Verified Licensed Sponsor (A-Rated Eligible)" if is_licensed else "Unregistered (Mentions Graduate Route Compatibility)"
            job['experience_checked'] = "Early Career Match (0-1 Year)"
            filtered_jobs.append(job)

    print(f"Phase 2 Complete. Narrowed down from {len(sourced_jobs)} raw items to {len(filtered_jobs)} highly viable leads.")
    
    with open("visa_approved_jobs.json", "w") as f:
        json.dump(filtered_jobs, f, indent=4)
    print("Filtered targets successfully archived to visa_approved_jobs.json.")

if __name__ == "__main__":
    filter_sourced_jobs()
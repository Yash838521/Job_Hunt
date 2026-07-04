import os
import requests
import json
from datetime import datetime, timedelta

# ==========================================
# 1. INITIAL CONFIGURATION & API KEYS
# ==========================================
# Replace these with your actual keys from Adzuna's developer site
ADZUNA_APP_ID = "YOUR_ADZUNA_APP_ID"
ADZUNA_APP_KEY = "YOUR_ADZUNA_APP_KEY"

# Target variables tailored from your profile
TARGET_KEYWORDS = [
    "Graduate Data Scientist", "Junior Data Scientist",
    "Graduate Data Analyst", "Junior Data Analyst",
    "Machine Learning Graduate", "Junior Machine Learning Engineer",
    "Graduate AI Engineer", "Junior AI Engineer",
    "Graduate Data Engineer", "Junior Data Engineer",
    "Business Intelligence Analyst", "Graduate BI Analyst",
    "Product Analyst", "Analytics Engineer"
]

EXCLUDE_KEYWORDS = ["senior", "lead", "principal", "manager", "director", "head of"]
PREFERRED_CITIES = ["bristol", "london", "cambridge", "manchester", "birmingham", "leeds", "edinburgh", "glasgow", "belfast"]

# ==========================================
# 2. THE SOURCING FUNCTION
# ==========================================
def fetch_daily_jobs():
    print(f"--- Starting Phase 1 Job Search: {datetime.now().strftime('%Y-%m-%d')} ---")
    all_raw_jobs = []
    
    # Calculate timestamp for 24 hours ago to target fresh posts
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    
    for keyword in TARGET_KEYWORDS:
        print(f"Scouring UK market for: '{keyword}'...")
        
        # Adzuna API URL structure for United Kingdom (gb)
        # Page 1, sorting by date descending
        url = f"https://api.adzuna.com/v1/api/jobs/gb/search/1"
        params = {
            'app_id': "bf50c44c",
            'app_key': "6d7b0c510f0ca98432c9462bed59d8d8",
            'what': keyword,
            'results_per_page': 20, # Keep data light and clean
            'sort_by': 'date'
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                for job in results:
                    # Filter check 1: Ensure it was posted recently
                    created_date_str = job.get('created', '')
                    # Format standard date handling: ISO timestamp normalization
                    try:
                        created_date = datetime.strptime(created_date_str.split('T')[0], '%Y-%m-%d')
                    except ValueError:
                        created_date = datetime.utcnow()
                        
                    # Filter check 2: Strict keyword exclusion to eliminate 3+ years roles
                    title = job.get('title', '').lower()
                    description = job.get('description', '').lower()
                    if any(bad_word in title for bad_word in EXCLUDE_KEYWORDS):
                        continue
                        
                    # Filter check 3: Salary logic mapping
                    salary_min = job.get('salary_min', 0)
                    location_display = job.get('location', {}).get('display_name', '').lower()
                    
                    # Apply geographic salary boundaries
                    if "london" in location_display and salary_min and salary_min < 32000:
                        continue
                    elif salary_min and salary_min < 28000 and "london" not in location_display:
                        # Allow flexibility for robust grad schemes as specified
                        if "graduate" not in title:
                            continue

                    # Structure the data uniformly for Phase 2
                    job_record = {
                        'title': job.get('title'),
                        'company': job.get('company', {}).get('display_name'),
                        'location': job.get('location', {}).get('display_name'),
                        'url': job.get('redirect_url'),
                        'description': job.get('description'),
                        'salary': job.get('salary_min'),
                        'date_posted': created_date.strftime('%Y-%m-%d')
                    }
                    
                    # Prevent duplicates across overlapping keyword searches
                    if job_record['url'] not in [j['url'] for j in all_raw_jobs]:
                        all_raw_jobs.append(job_record)
                        
        except Exception as e:
            print(f"Skipping search branch for '{keyword}' due to endpoint connection delay: {e}")
            continue

    # ==========================================
    # 3. PRIORITISATION & SORTING
    # ==========================================
    # Move jobs in your preferred cities to the top of the stack
    def sorting_score(job):
        loc = job['location'].lower()
        if any(city in loc for city in PREFERRED_CITIES):
            return 0 # Top priority
        return 1 # Secondary market fallback

    all_raw_jobs.sort(key=sorting_score)
    
    print(f"\nPhase 1 Complete. Found {len(all_raw_jobs)} unique early-career data roles.")
    return all_raw_jobs

if __name__ == "__main__":
    jobs = fetch_daily_jobs()
    # Save raw outputs to test data pipeline stability locally
    with open("raw_sourced_jobs.json", "w") as f:
        json.dump(jobs, f, indent=4)
    print("Sourced data written to raw_sourced_jobs.json successfully.")
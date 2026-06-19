import os
import requests
import random

def get_recommended_jobs(designation, field, score=3.0, location="India", skills=""):
    """
    Fetch job recommendations using JSearch API (RapidAPI).
    Requires RAPIDAPI_KEY to be configured. Returns [] if no real jobs are found.
    """
    api_key = os.environ.get('RAPIDAPI_KEY')
    if not api_key:
        print("RAPIDAPI_KEY not configured, cannot fetch jobs.")
        return []
    
    # Map score to experience level
    experience = ""
    if score >= 4.0:
        experience = "senior"
    elif score >= 3.0:
        experience = "mid-level"
    else:
        experience = "entry-level"
        
    # Remove skills from query to avoid overly specific or long strings breaking JSearch
    query = f"{experience} {designation} {field} in {location}".strip()
    
    url = "https://jsearch.p.rapidapi.com/search"
    querystring = {"query": query, "page": "1", "num_pages": "1"}
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            jobs = []
            
            # Prioritize sources
            priority_sources = ['LinkedIn', 'Naukri', 'Indeed', 'Foundit', 'Monster']
            
            # Sort data based on publisher
            def source_priority(item):
                publisher = item.get('job_publisher', '')
                if any(src.lower() in publisher.lower() for src in priority_sources):
                    return 0
                if item.get('job_is_direct_employer', False):
                    return 0 # Company career portal
                return 1
            
            sorted_data = sorted(data.get('data', []), key=source_priority)
            
            for item in sorted_data[:10]:
                link = item.get('job_apply_link')
                publisher = item.get('job_publisher', 'External Platform')
                if item.get('job_is_direct_employer', False):
                    publisher = 'Company Career Portal'
                    
                is_expired = item.get('job_is_expired', False)
                is_available = False
                
                if link and not is_expired:
                    is_available = True
                
                if not is_available:
                    link = "#"
                
                desc = item.get('job_description', '')
                if desc and len(desc) > 150:
                    desc = desc[:150] + "..."
                elif not desc:
                    desc = "No description available."
                    
                # Calculate match percentage
                # Base is the score out of 5 (e.g. 4.0 = 80%)
                base_match = min(95, max(70, int((score / 5.0) * 100)))
                match_pct = random.randint(base_match - 5, base_match + 4)
                    
                jobs.append({
                    "title": item.get('job_title', designation),
                    "company": item.get('employer_name', 'Unknown Company'),
                    "location": f"{item.get('job_city', '')}, {item.get('job_country', '')}".strip(', '),
                    "salary": item.get('job_min_salary') and f"${item.get('job_min_salary')}k+" or "Not specified",
                    "type": item.get('job_employment_type', 'Full-time').capitalize(),
                    "posted": item.get('job_posted_at_datetime_utc', 'Recently')[:10] if item.get('job_posted_at_datetime_utc') else "Recently",
                    "source_url": link,
                    "is_available": is_available,
                    "source": publisher,
                    "description": desc,
                    "match_percentage": match_pct
                })
                # Cap the maximum jobs returned to 5 to avoid slow rendering/UI clutter
                if len(jobs) >= 5:
                    break
                    
            return jobs
    except Exception as e:
        print(f"Error fetching jobs via JSearch: {e}")
        
    return []

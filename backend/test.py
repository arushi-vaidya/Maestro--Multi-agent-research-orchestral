def get_trial_summary_v2(nct_id):
    """
    Fetch and print a short summary (brief title and brief summary) for a given NCT ID.
    """
    url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch study {nct_id}: {response.status_code}")
        return
    data = response.json()
    try:
        id_mod = data['protocolSection']['identificationModule']
        title = id_mod.get('briefTitle', 'N/A')
        summary = data['protocolSection'].get('descriptionModule', {}).get('briefSummary', 'No summary available.')
        print(f"NCT ID: {nct_id}\nTitle: {title}\nSummary: {summary[:400]}{'...' if len(summary) > 400 else ''}")
    except Exception as e:
        print(f"Error extracting summary: {e}")

import requests

def search_studies_v2(term, page_size=5, fields=None):
    url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.term": term,
        "pageSize": page_size
    }
    if fields:
        params["fields"] = ",".join(fields)
    response = requests.get(url, params=params)
    print("Status code:", response.status_code)
    print("Response text:", response.text[:500])
    if response.headers.get("Content-Type", "").startswith("application/json"):
        data = response.json()
        return data
    else:
        print("Response is not JSON!")
        return None

if __name__ == "__main__":
    result = search_studies_v2("diabetes metformin", page_size=5, fields=["NCTId", "BriefTitle"])
    print(result)
    # Example: print a short summary for the first returned NCT ID
    if result and 'studies' in result and result['studies']:
        nct_id = result['studies'][0]['protocolSection']['identificationModule']['nctId']
        print("\nShort summary for first trial:")
        get_trial_summary_v2(nct_id)
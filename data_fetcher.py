import feedparser
import pandas as pd
from datetime import datetime, timedelta
import ssl
import re
from bs4 import BeautifulSoup
import concurrent.futures
import warnings

warnings.filterwarnings("ignore")

# Configure SSL once at the module level
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

# RSS feed sources focused on AI in medicine/healthcare
AI_MEDICINE_FEEDS = {
    "https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml": "Science Daily",
    "https://www.nature.com/subjects/medical-research.rss": "Nature",
    "https://www.technologyreview.com/feed/": "MIT Technology Review",
    "https://medicalfuturist.com/feed/": "Medical Futurist",
    "https://venturebeat.com/category/ai/feed/": "VentureBeat",
    "https://blogs.bmj.com/bmj/category/artificial-intelligence/feed/": "BMJ",
    "https://www.healthcareitnews.com/taxonomy/term/8601/feed": "Healthcare IT News",
    "https://www.frontiersin.org/journals/digital-health/rss": "Frontiers in Digital Health"
}

# Medical AI research topics for filtering
MEDICAL_AI_TOPICS = [
    "Medical Imaging", 
    "NLP in Healthcare", 
    "Clinical Decision Support", 
    "Drug Discovery", 
    "Predictive Analytics", 
    "Disease Diagnosis", 
    "Electronic Health Records", 
    "Personalized Medicine", 
    "Patient Monitoring", 
    "Genomics"
]

# Keywords associated with each topic for filtering
TOPIC_KEYWORDS = {
    "Medical Imaging": ["imaging", "radiology", "x-ray", "mri", "ct scan", "ultrasound", "image segmentation", "image classification"],
    "NLP in Healthcare": ["nlp", "natural language", "text mining", "medical notes", "clinical notes", "documentation", "medical language"],
    "Clinical Decision Support": ["clinical decision", "decision support", "cdss", "clinical workflow", "physician", "doctor", "nurse", "medical decision"],
    "Drug Discovery": ["drug discovery", "pharmaceutical", "molecule", "compound", "drug design", "medicinal chemistry", "therapeutics"],
    "Predictive Analytics": ["predict", "forecasting", "risk prediction", "outcome prediction", "patient outcome", "mortality prediction", "readmission"],
    "Disease Diagnosis": ["diagnosis", "diagnostic", "detection", "screening", "early detection", "disease classification", "pathology"],
    "Electronic Health Records": ["ehr", "emr", "electronic health record", "electronic medical record", "health record", "patient record"],
    "Personalized Medicine": ["personalized", "precision medicine", "patient-specific", "tailored", "individualized care", "custom treatment"],
    "Patient Monitoring": ["monitoring", "wearable", "sensor", "remote monitoring", "patient tracking", "vital signs", "telehealth"],
    "Genomics": ["genomic", "gene", "genetic", "dna", "rna", "sequencing", "genome", "biomarker"]
}

def clean_html(text):
    """Clean HTML tags from text"""
    try:
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text().strip()
    except Exception as e:
        print(f"Error cleaning HTML: {e}")
        return text

def extract_date(date_str):
    """Extract date from various formats using regex patterns"""
    try:
        # Pattern 1: Standard RFC format like "Mon, 14 Apr 2025 10:00:00 GMT"
        pattern1 = r'(?:\w+,\s+)?(\d{1,2}\s+\w{3}\s+\d{4})'
        match = re.search(pattern1, date_str)
        if match:
            date_str = match.group(1)
            return pd.to_datetime(date_str, format='%d %b %Y')
        
        # Pattern 2: ISO format like "2025-04-14"
        pattern2 = r'(\d{4}-\d{2}-\d{2})'
        match = re.search(pattern2, date_str)
        if match:
            return pd.to_datetime(match.group(1))
        
        # If none of the patterns match, return NaT
        return pd.NaT
    except:
        return pd.NaT

def fetch_single_feed(link_source_tuple):
    """Fetch a single RSS feed and return its entries"""
    link, source = link_source_tuple
    entries = {"Title": [], "Link": [], "Published": [], "Description": [], "Source": []}
    
    try:
        feed = feedparser.parse(link)
        
        for entry in feed.entries:
            entries["Title"].append(entry.get("title", "No Title"))
            entries["Link"].append(entry.get("link", "No Link"))
            entries["Published"].append(entry.get("published", "No Date"))
            
            # Get description from different possible fields
            description = entry.get("description", "")
            if not description:
                description = entry.get("summary", "")
            if not description:
                description = entry.get("content", [{"value": ""}])[0].get("value", "")
            
            entries["Description"].append(description)
            entries["Source"].append(source)
            
    except Exception as e:
        print(f"Error fetching {link}: {e}")
    
    return entries

def fetch_arxiv_papers(query, max_results=50):
    """Fetch papers from arXiv API based on query"""
    base_url = "http://export.arxiv.org/api/query?"
    
    # Construct the query
    search_query = f"search_query={query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    url = base_url + search_query
    
    try:
        # Parse the arXiv API response
        feed = feedparser.parse(url)
        
        entries = {
            "Title": [], 
            "Link": [], 
            "Published": [], 
            "Description": [], 
            "Source": []
        }
        
        for entry in feed.entries:
            entries["Title"].append(entry.get("title", "").replace("\n", " "))
            entries["Link"].append(entry.get("link", ""))
            entries["Published"].append(entry.get("published", ""))
            
            # Extract summary and remove newlines
            summary = entry.get("summary", "").replace("\n", " ")
            entries["Description"].append(summary)
            entries["Source"].append("arXiv")
        
        return pd.DataFrame(entries)
    
    except Exception as e:
        print(f"Error fetching data from arXiv: {e}")
        return pd.DataFrame()

def process_data(df):
    """Process and clean the news data"""
    if df.empty:
        return df
        
    try:
        # Apply the date extraction function
        df['date'] = df['Published'].apply(extract_date)
        
        # Drop rows with invalid dates
        df = df.dropna(subset=['date'])
        
        # Clean HTML and limit description length
        df['Description'] = df['Description'].apply(
            lambda x: clean_html(x)[:300] + '...' if len(clean_html(x)) > 300 else clean_html(x)
        )
        
        # Drop the original 'Published' column
        df = df.drop(columns=['Published'], errors='ignore')
        
        # Sort by date in descending order
        df = df.sort_values(by='date', ascending=False)
        
        # Detect topics based on keywords
        for topic, keywords in TOPIC_KEYWORDS.items():
            # Check if title or description contains any of the keywords
            df[topic] = df.apply(
                lambda row: any(keyword.lower() in (row['Title'].lower() + " " + row['Description'].lower()) 
                              for keyword in keywords),
                axis=1
            )
        
        return df
        
    except Exception as e:
        print(f"An error occurred while processing the data: {e}")
        return pd.DataFrame()

def fetch_all_feeds(days=30):
    """Fetch all configured RSS feeds and arXiv papers"""
    all_entries = {"Title": [], "Link": [], "Published": [], "Description": [], "Source": []}
    
    # Use ThreadPoolExecutor to fetch RSS feeds in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_link = {executor.submit(fetch_single_feed, (link, source)): (link, source) 
                         for link, source in AI_MEDICINE_FEEDS.items()}
        
        for future in concurrent.futures.as_completed(future_to_link):
            link, source = future_to_link[future]
            try:
                result = future.result()
                # Merge results into all_entries
                for key in all_entries:
                    all_entries[key].extend(result[key])
            except Exception as e:
                print(f"Exception for {link}: {e}")
    
    # Create a DataFrame from all RSS entries
    rss_df = pd.DataFrame(all_entries)
    
    # Fetch arXiv papers
    arxiv_query = "(cat:cs.AI OR cat:cs.LG OR cat:stat.ML) AND (medicine OR healthcare OR clinical OR medical)"
    arxiv_df = fetch_arxiv_papers(arxiv_query)
    
    # Combine both sources
    combined_df = pd.concat([rss_df, arxiv_df], ignore_index=True)
    
    # Process the combined data
    processed_df = process_data(combined_df)
    
    # Filter for the specified time period
    if not processed_df.empty:
        today = datetime.now()
        past_date = today - timedelta(days=days)
        processed_df = processed_df[(processed_df['date'] >= past_date)]
    
    return processed_df

def get_ai_medicine_news(days=30):
    """Main function to get AI in medicine news"""
    return fetch_all_feeds(days)

if __name__ == "__main__":
    # Test the function
    df = get_ai_medicine_news(days=30)
    print(f"Found {len(df)} articles")
    if not df.empty:
        print(df.head())
        # Save to Excel for testing
        df.to_excel("ai_medicine_news.xlsx")
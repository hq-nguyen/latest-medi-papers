# AI in Medicine News Dashboard

A Streamlit-powered dashboard for tracking the latest research and developments at the intersection of artificial intelligence and medicine. This application fetches and aggregates news from multiple sources including RSS feeds and arXiv papers, then categorizes them by relevant medical AI topics.

## Features

- Aggregates news from multiple sources:
  - Popular RSS feeds (Science Daily, Nature, MIT Technology Review, etc.)
  - arXiv research papers at the intersection of AI and medicine
- Filters content by:
  - Date range
  - Medical AI topics (Medical Imaging, NLP in Healthcare, Drug Discovery, etc.)
  - News sources
- Multiple viewing options:
  - Card view with detailed information
  - Table view for quick scanning
- Automatic topic detection using keyword analysis
- Cached data fetching for improved performance

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/ai-medicine-news.git
   cd ai-medicine-news
   ```

2. Install the required dependencies:
   ```
   pip install streamlit pandas feedparser beautifulsoup4
   ```

## Usage

Run the Streamlit application:
```
streamlit run main.py
```

The dashboard will open in your default web browser. From there, you can:
- Browse the latest AI in medicine news
- Filter articles by date, topic, and source
- View article details and follow links to the original content

## Project Structure

- `main.py`: The Streamlit interface and dashboard functionality
- `data_fetcher.py`: Handles all data acquisition from RSS feeds and arXiv

## Configuration

You can modify the following in `data_fetcher.py`:
- `AI_MEDICINE_FEEDS`: Dictionary of RSS feed URLs and their source names
- `MEDICAL_AI_TOPICS`: List of AI in medicine topics for categorization
- `TOPIC_KEYWORDS`: Keywords associated with each topic for automatic classification

## Customization

To add or modify news sources:
1. Open `data_fetcher.py`
2. Add new URLs to the `AI_MEDICINE_FEEDS` dictionary
3. Refresh the data in the dashboard

To add new topics:
1. Add the topic name to `MEDICAL_AI_TOPICS` list
2. Add associated keywords to the `TOPIC_KEYWORDS` dictionary

## Requirements

- Python 3.7+
- Streamlit
- Pandas
- Feedparser
- BeautifulSoup4

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
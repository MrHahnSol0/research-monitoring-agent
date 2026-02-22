#!/usr/bin/env python3
"""
Research Monitoring Agent - Phase 1
Aggregates RSS feeds from core sources and prepares for AI curation
Author: Maj Jared Juntunen
Created: 2025-02-15
"""

import feedparser
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict
import time

@dataclass
class Article:
    """Represents a single article from a source"""
    title: str
    url: str
    source: str
    published: str
    summary: str
    themes: List[str]  # Will be populated by AI curation

# Core RSS sources for Week 1
RSS_SOURCES = {
    "War on the Rocks": {
        "url": "https://warontherocks.com/feed/",
        "themes": ["JADO", "PME Innovation", "Current Conflicts"]
    },
    "Breaking Defense": {
        "url": "https://breakingdefense.com/feed/",
        "themes": ["JADO", "AI/ML Military", "JADC2"]
    },
    "Defense One": {
        "url": "https://www.defenseone.com/rss/technology/",
        "themes": ["AI/ML Military"]
    },
    "C4ISRNET": {
        "url": "https://www.c4isrnet.com/arc/outboundfeeds/rss/",
        "themes": ["JADC2"]
    },
    "Modern War Institute": {
        "url": "https://mwi.westpoint.edu/feed/",
        "themes": ["PME Innovation", "Current Conflicts"]
    },
    "Institute for the Study of War": {
        "url": "https://www.understandingwar.org/rss.xml",
        "themes": ["Current Conflicts"]
    },
    "DARPA": {
        "url": "https://www.darpa.mil/rss.xml",
        "themes": ["Quantum Technology"]
    },
    "Anthropic": {
        "url": "https://www.anthropic.com/news/rss.xml",
        "themes": ["AI/ML Military"]
    },
    "USNI Proceedings": {
        "url": "https://www.usni.org/magazines/proceedings/rss",
        "themes": ["JADO", "Current Conflicts"]
}
}
def fetch_articles(hours_lookback: int = 24) -> List[Article]:
    """
    Fetch articles from all RSS sources published within lookback window
    
    Args:
        hours_lookback: How many hours back to fetch articles (default 24)
    
    Returns:
        List of Article objects
    """
    articles = []
    cutoff_time = datetime.now() - timedelta(hours=hours_lookback)
    
    print(f"Fetching articles from last {hours_lookback} hours...")
    print(f"Cutoff time: {cutoff_time}\n")
    
    for source_name, source_config in RSS_SOURCES.items():
        print(f"Fetching from {source_name}...")
        
        try:
            feed = feedparser.parse(source_config["url"])
            
            for entry in feed.entries:
                # Parse published date (RSS feeds use different formats)
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])
                
                # Only include recent articles
                if pub_date and pub_date >= cutoff_time:
                    article = Article(
                        title=entry.title,
                        url=entry.link,
                        source=source_name,
                        published=pub_date.strftime("%Y-%m-%d %H:%M"),
                        summary=entry.get('summary', '')[:300],  # Truncate long summaries
                        themes=source_config["themes"]  # Initial theme assignment
                    )
                    articles.append(article)
            
            print(f"  Found {len([a for a in articles if a.source == source_name])} recent articles")
            time.sleep(1)  # Be polite to servers
            
        except Exception as e:
            print(f"  Error fetching {source_name}: {str(e)}")
    
    print(f"\nTotal articles fetched: {len(articles)}\n")
    return articles

def save_articles(articles: List[Article], filename: str = "articles_raw.json"):
    """Save articles to JSON file for AI curation"""
    with open(filename, 'w') as f:
        json.dump([asdict(a) for a in articles], f, indent=2)
    print(f"Saved {len(articles)} articles to {filename}")

def load_articles(filename: str = "articles_raw.json") -> List[Article]:
    """Load articles from JSON file"""
    with open(filename, 'r') as f:
        data = json.load(f)
    return [Article(**item) for item in data]

def display_summary(articles: List[Article]):
    """Display summary of fetched articles by source and theme"""
    print("\n" + "="*60)
    print("FETCH SUMMARY")
    print("="*60)
    
    # By source
    print("\nArticles by Source:")
    source_counts = {}
    for article in articles:
        source_counts[article.source] = source_counts.get(article.source, 0) + 1
    
    for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count}")
    
    # By theme (articles can have multiple themes)
    print("\nArticles by Theme:")
    theme_counts = {}
    for article in articles:
        for theme in article.themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
    
    for theme, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {theme}: {count}")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    # Fetch articles from last 48 hours
    articles = fetch_articles(hours_lookback=48)
    
    # Display summary
    display_summary(articles)
    
    # Save for AI curation
    save_articles(articles)
    
    print("Next step: Run AI curation on articles_raw.json")
    print("Command: python3 curate_articles.py")

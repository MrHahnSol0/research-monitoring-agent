#!/usr/bin/env python3
"""
AI Curation Engine - Production Version
Uses Anthropic API to evaluate articles against research themes
Author: Maj Jared Juntunen
Created: 2025-02-15
Updated: 2025-02-17 - Added real API integration
"""

import json
import os
from typing import List, Dict
from dataclasses import dataclass, asdict
from datetime import datetime

# Import Anthropic SDK
try:
    from anthropic import Anthropic
except ImportError:
    print("ERROR: anthropic package not installed")
    print("Run: pip install anthropic --break-system-packages")
    exit(1)

# Import API key from config
try:
    from config import ANTHROPIC_API_KEY
except ImportError:
    print("ERROR: config.py not found")
    print("Create config.py with your API key:")
    print('ANTHROPIC_API_KEY = "sk-ant-your-key-here"')
    exit(1)

@dataclass
class CuratedArticle:
    """Article with AI-generated relevance scoring"""
    title: str
    url: str
    source: str
    published: str
    summary: str
    primary_theme: str
    relevance_score: int  # 1-10
    relevance_explanation: str
    cross_theme_connections: List[str]
    jj_insight: str

# Research theme definitions
THEME_DEFINITIONS = """
1. JADO (Joint All-Domain Operations): Concepts, doctrine, and implementation of multi-domain warfare. Focus on operational implications for field-grade officers and integration challenges.

2. AI/ML Military: Applications of artificial intelligence and machine learning in military decision-making, operations, and training. Emphasis on practical implementation over hype.

3. PME Innovation: Professional Military Education teaching methods, curriculum development, and educational technology. Focus on what makes officers better strategic thinkers.

4. Current Conflicts: New combat developments, tactical innovations, and operational lessons from ongoing conflicts (Ukraine, Middle East, etc.). Emphasis on what's genuinely new, not repetitive coverage.

5. JADC2: Joint All-Domain Command and Control systems, integration efforts, and technical implementation. Focus on operational implications, not just policy announcements.

6. Quantum Technology: Military applications of quantum computing, communications, and sensing. Research developments with near-term operational relevance.
"""

JJ_CONTEXT = """
Maj Jared Juntunen is a Marine Corps officer transitioning from HMX-1 to Marine Corps University as a Military Faculty Advisor. His focus is teaching Joint All-Domain Operations and strategic planning. He has strong technical AI/ML background and is building expertise in AI orchestration. He values:
- Operational implications over policy debate
- Cross-domain synthesis (articles connecting multiple themes)
- Primary source material over summaries
- Teaching applications for PME
- Real-world practitioner insights over theoretical frameworks

Articles that are "JJ-relevant" typically:
- Provide operational insights for field-grade officers
- Connect multiple domains or themes
- Offer teaching/learning applications
- Challenge conventional thinking with evidence
- Come from practitioners or serious researchers
"""

CURATION_PROMPT_TEMPLATE = """You are evaluating military/defense articles for relevance to a specific officer's research interests.

RESEARCH THEMES:
{theme_definitions}

READER CONTEXT:
{jj_context}

ARTICLE TO EVALUATE:
Title: {title}
Source: {source}
Published: {published}
Summary: {summary}
URL: {url}

TASK:
Evaluate this article's relevance to the research themes and reader context. Respond ONLY with valid JSON in this exact format:

{{
  "primary_theme": "one of: JADO, AI/ML Military, PME Innovation, Current Conflicts, JADC2, Quantum Technology, or NONE if not relevant",
  "relevance_score": [1-10 integer, where 10 = must-read, 5 = moderately useful, 1 = skip],
  "relevance_explanation": "2-3 sentence explanation of why this score",
  "cross_theme_connections": ["list", "of", "other", "themes", "this", "connects", "to"],
  "jj_insight": "One sentence on why this specifically matters for JJ's MCU role or research"
}}

Be honest about low relevance scores. Articles score high (8-10) only if they offer genuine operational insights, cross-domain synthesis, or teaching applications. Generic news or policy announcements should score 3-5. Pure hype or irrelevant content scores 1-2.
"""

def curate_article_with_claude(article: Dict, client: Anthropic) -> CuratedArticle:
    """
    Send article to Claude API for curation
    """
    
    # Build the prompt
    prompt = CURATION_PROMPT_TEMPLATE.format(
        theme_definitions=THEME_DEFINITIONS,
        jj_context=JJ_CONTEXT,
        title=article['title'],
        source=article['source'],
        published=article['published'],
        summary=article['summary'][:500],  # Truncate long summaries
        url=article['url']
    )
    
    try:
        # Call Anthropic API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the response
        response_text = message.content[0].text
        
        # Parse JSON response
        curation_data = json.loads(response_text)
        
        # Create CuratedArticle object
        return CuratedArticle(
            title=article['title'],
            url=article['url'],
            source=article['source'],
            published=article['published'],
            summary=article['summary'][:300],
            primary_theme=curation_data['primary_theme'],
            relevance_score=curation_data['relevance_score'],
            relevance_explanation=curation_data['relevance_explanation'],
            cross_theme_connections=curation_data.get('cross_theme_connections', []),
            jj_insight=curation_data['jj_insight']
        )
        
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse JSON for '{article['title'][:50]}...'")
        print(f"Response was: {response_text[:200]}")
        # Return low-scored placeholder
        return CuratedArticle(
            title=article['title'],
            url=article['url'],
            source=article['source'],
            published=article['published'],
            summary=article['summary'][:300],
            primary_theme="NONE",
            relevance_score=1,
            relevance_explanation="Failed to parse AI response",
            cross_theme_connections=[],
            jj_insight="Error in curation"
        )
    except Exception as e:
        print(f"Error curating '{article['title'][:50]}...': {str(e)}")
        return CuratedArticle(
            title=article['title'],
            url=article['url'],
            source=article['source'],
            published=article['published'],
            summary=article['summary'][:300],
            primary_theme="NONE",
            relevance_score=1,
            relevance_explanation=f"Error: {str(e)}",
            cross_theme_connections=[],
            jj_insight="Error in curation"
        )

def generate_digest(curated_articles: List[CuratedArticle], min_score: int = 6) -> str:
    """Generate the daily digest in readable format"""
    
    # Filter by minimum relevance score
    high_value = [a for a in curated_articles if a.relevance_score >= min_score]
    high_value.sort(key=lambda x: x.relevance_score, reverse=True)
    
    digest = []
    digest.append("="*80)
    digest.append("STRATEGIC READING DIGEST")
    digest.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    digest.append(f"Articles reviewed: {len(curated_articles)} | High-value (≥{min_score}/10): {len(high_value)}")
    digest.append("="*80)
    digest.append("")
    
    if not high_value:
        digest.append("No high-value articles found in this batch.")
        digest.append("Consider lowering min_score or adjusting source selection.")
        return "\n".join(digest)
    
    # Top 3 must-reads
    digest.append("🎯 YOUR TOP 3 MUST-READS (12-minute morning read)")
    digest.append("="*80)
    digest.append("")
    
    for i, article in enumerate(high_value[:3], 1):
        digest.append(f"{i}. [SCORE: {article.relevance_score}/10] {article.title}")
        digest.append(f"   {article.source} | {article.published}")
        digest.append(f"   {article.url}")
        digest.append(f"   Theme: {article.primary_theme}")
        digest.append(f"   ")
        digest.append(f"   {article.relevance_explanation}")
        digest.append(f"   → {article.jj_insight}")
        if article.cross_theme_connections:
            digest.append(f"   Connects to: {', '.join(article.cross_theme_connections)}")
        digest.append("")
    
    # Rest organized by theme
    if len(high_value) > 3:
        digest.append("\n" + "="*80)
        digest.append(f"ADDITIONAL HIGH-VALUE ARTICLES ({len(high_value) - 3} more)")
        digest.append("="*80)
        digest.append("")
        
        # Group by theme
        by_theme = {}
        for article in high_value[3:]:
            if article.primary_theme not in by_theme:
                by_theme[article.primary_theme] = []
            by_theme[article.primary_theme].append(article)
        
        for theme, articles in sorted(by_theme.items()):
            digest.append(f"\n{theme} ({len(articles)} articles)")
            digest.append("─"*80)
            
            for article in articles:
                digest.append(f"\n[{article.relevance_score}/10] {article.title}")
                digest.append(f"{article.source} | {article.url}")
                digest.append(f"{article.relevance_explanation}")
                digest.append("")
    
    # Statistics
    digest.append("\n" + "="*80)
    digest.append("DIGEST STATISTICS")
    digest.append("="*80)
    
    theme_counts = {}
    for article in high_value:
        theme_counts[article.primary_theme] = theme_counts.get(article.primary_theme, 0) + 1
    
    digest.append("\nHigh-value articles by theme:")
    for theme, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True):
        digest.append(f"  {theme}: {count}")
    
    digest.append("\n" + "="*80)
    digest.append("END OF DIGEST")
    digest.append("="*80)
    
    return "\n".join(digest)

def main():
    """Main curation pipeline"""
    
    print("="*60)
    print("AI Curation Engine - Production Version")
    print("="*60)
    print()
    
    # Initialize Anthropic client
    print("Initializing Anthropic API client...")
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    print("✓ Connected to Claude API")
    print()
    
    # Load raw articles
    try:
        with open('articles_raw.json', 'r', encoding='utf-8') as f:
            articles = json.load(f)
        print(f"✓ Loaded {len(articles)} articles for curation")
    except FileNotFoundError:
        print("✗ ERROR: articles_raw.json not found")
        print("Run research_monitor.py first to fetch articles")
        return
    
    if not articles:
        print("No articles to curate. Exiting.")
        return
    
    print()
    print("Starting curation (this will take ~30 seconds)...")
    print()
    
    # Curate each article
    curated_articles = []
    for i, article in enumerate(articles, 1):
        print(f"[{i}/{len(articles)}] Curating: {article['title'][:60]}...")
        curated = curate_article_with_claude(article, client)
        curated_articles.append(curated)
    
    print()
    print(f"✓ Curated {len(curated_articles)} articles")
    
    # Save curated results
    with open('articles_curated.json', 'w', encoding='utf-8') as f:
        json.dump([asdict(a) for a in curated_articles], f, indent=2)
    print("✓ Saved curated data to articles_curated.json")
    
    # Generate digest
    digest = generate_digest(curated_articles, min_score=6)
    
    # Save digest
    with open('digest.txt', 'w', encoding='utf-8') as f:
        f.write(digest)
    print("✓ Saved digest to digest.txt")
    
    # Display digest
    print()
    print(digest)
    
    # Cost estimate
    print()
    print("="*60)
    print("COST ESTIMATE")
    print("="*60)
    estimated_cost = len(articles) * 0.003  # Rough estimate
    print(f"Approximate API cost: ${estimated_cost:.2f}")
    print("(Actual cost visible in Anthropic console)")

if __name__ == "__main__":
    main()

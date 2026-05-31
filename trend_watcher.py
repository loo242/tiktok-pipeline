import os
import requests
import feedparser
from datetime import datetime

AIRTABLE_TOKEN = os.environ['AIRTABLE_TOKEN']
AIRTABLE_BASE_ID = os.environ['AIRTABLE_BASE_ID']

def get_google_trends_rss():
    try:
        url = 'https://trends.google.com/trends/trendingsearches/daily/rss?geo=US'
        feed = feedparser.parse(url)
        topics = []
        for entry in feed.entries[:10]:
            topics.append({
                'topic': entry.title,
                'source': 'google_trends',
                'hashtags': ''
            })
        print(f"Google Trends RSS: {len(topics)} topics")
        return topics
    except Exception as e:
        print(f"Google Trends RSS error: {e}")
        return []

def get_rss_trends():
    feeds = [
        'https://feeds.bbci.co.uk/news/rss.xml',
        'https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en'
    ]
    topics = []
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                topics.append({
                    'topic': entry.title,
                    'source': 'rss_news',
                    'hashtags': ''
                })
        except Exception as e:
            print(f"RSS error for {feed_url}: {e}")
    print(f"RSS feeds: {len(topics)} topics")
    return topics

def score_topics(all_topics):
    scores = {}
    for item in all_topics:
        topic = item['topic'].lower().strip()
        if topic not in scores:
            scores[topic] = {
                'topic': item['topic'],
                'score': 0,
                'sources': set(),
                'hashtags': item['hashtags']
            }
        scores[topic]['score'] += 1
        scores[topic]['sources'].add(item['source'])
        if item['hashtags']:
            scores[topic]['hashtags'] = item['hashtags']

    ranked = sorted(scores.values(), key=lambda x: x['score'], reverse=True)
    return ranked[:5]

def save_to_airtable(topics):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Trends"
    headers = {
        'Authorization': f'Bearer {AIRTABLE_TOKEN}',
        'Content-Type': 'application/json'
    }
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    records = []
    for t in topics:
        records.append({
            'fields': {
                'Topic': t['topic'],
                'Score': t['score'],
                'Sources': ', '.join(t['sources']),
                'Hashtags': t['hashtags'],
                'Recorded at': now
            }
        })
    response = requests.post(url, json={'records': records}, headers=headers)
    print(f"Airtable save: status {response.status_code}")
    if response.status_code != 200:
        print(response.text)

if __name__ == '__main__':
    print("Starting trend watcher...")
    all_topics = []
    all_topics += get_google_trends_rss()
    all_topics += get_rss_trends()
    print(f"Total raw topics: {len(all_topics)}")
    top5 = score_topics(all_topics)
    print(f"Top 5 trends: {[t['topic'] for t in top5]}")
    save_to_airtable(top5)
    print("Done")

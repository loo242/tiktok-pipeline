import os
import json
import requests
import feedparser
from datetime import datetime
from pytrends.request import TrendReq

AIRTABLE_TOKEN = os.environ['AIRTABLE_TOKEN']
AIRTABLE_BASE_ID = os.environ['AIRTABLE_BASE_ID']
APIFY_TOKEN = os.environ['APIFY_TOKEN']

def get_google_trends():
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        trending = pytrends.trending_searches(pn='united_states')
        topics = trending[0].tolist()[:10]
        print(f"Google Trends: {len(topics)} topics")
        return [{'topic': t, 'source': 'google_trends', 'hashtags': ''} for t in topics]
    except Exception as e:
        print(f"Google Trends error: {e}")
        return []

def get_rss_trends():
    feeds = [
        'https://feeds.bbci.co.uk/news/rss.xml',
        'https://feeds.reuters.com/reuters/topNews',
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

def get_apify_trends():
    try:
        run_url = "https://api.apify.com/v2/acts/clockworks~tiktok-scraper/runs"
        headers = {'Authorization': f'Bearer {APIFY_TOKEN}'}
        payload = {
            'searchQueries': ['trending'],
            'resultsType': 'hashtag',
            'maxResultsPerQuery': 10
        }
        response = requests.post(run_url, json=payload, headers=headers)
        run = response.json()
        run_id = run.get('data', {}).get('id')
        if not run_id:
            print("Apify: could not start run")
            return []

        import time
        for _ in range(12):
            time.sleep(10)
            status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
            status = requests.get(status_url, headers=headers).json()
            if status.get('data', {}).get('status') == 'SUCCEEDED':
                break

        dataset_id = status.get('data', {}).get('defaultDatasetId')
        items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
        items = requests.get(items_url, headers=headers).json()

        topics = []
        for item in items[:10]:
            tag = item.get('name', '')
            if tag:
                topics.append({
                    'topic': tag,
                    'source': 'apify_tiktok',
                    'hashtags': f'#{tag}'
                })
        print(f"Apify: {len(topics)} topics")
        return topics
    except Exception as e:
        print(f"Apify error: {e}")
        return []

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
    all_topics += get_google_trends()
    all_topics += get_rss_trends()
    all_topics += get_apify_trends()
    print(f"Total raw topics: {len(all_topics)}")
    top5 = score_topics(all_topics)
    print(f"Top 5 trends: {[t['topic'] for t in top5]}")
    save_to_airtable(top5)
    print("Done")

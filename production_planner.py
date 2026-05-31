import os
import json
import random
import requests
from datetime import datetime

AIRTABLE_TOKEN = os.environ['AIRTABLE_TOKEN']
AIRTABLE_BASE_ID = os.environ['AIRTABLE_BASE_ID']

def get_assets():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Assets"
    headers = {'Authorization': f'Bearer {AIRTABLE_TOKEN}'}
    response = requests.get(url, headers=headers)
    records = response.json().get('records', [])
    assets = []
    for r in records:
        fields = r.get('fields', {})
        if fields.get('File ID'):
            assets.append({
                'record_id': r['id'],
                'file_id': fields.get('File ID', ''),
                'filename': fields.get('Filename', ''),
                'file_type': fields.get('File type', '')
            })
    print(f"Found {len(assets)} assets")
    return assets

def get_top_trend():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Trends"
    headers = {'Authorization': f'Bearer {AIRTABLE_TOKEN}'}
    params = {'sort[0][field]': 'Score', 'sort[0][direction]': 'desc', 'maxRecords': 1}
    response = requests.get(url, headers=headers, params=params)
    records = response.json().get('records', [])
    if not records:
        print("No trends found")
        return None
    fields = records[0].get('fields', {})
    trend = {
        'topic': fields.get('Topic', ''),
        'hashtags': fields.get('Hashtags', ''),
        'score': fields.get('Score', 0)
    }
    print(f"Top trend: {trend['topic']}")
    return trend

def pick_clips(assets):
    videos = [a for a in assets if 'video' in a.get('file_type', '').lower()]
    if not videos:
        videos = assets
    count = min(3, len(videos))
    picked = random.sample(videos, count)
    print(f"Picked {len(picked)} clips")
    return picked

def build_plan(trend, clips):
    topic = trend['topic']
    hashtags = trend['hashtags']

    hook_templates = [
        f"POV: you just discovered {topic}",
        f"Nobody is talking about {topic} — but they should be",
        f"Everything you need to know about {topic} in 15 seconds",
        f"Wait until you hear about {topic}",
        f"This {topic} story will surprise you"
    ]

    script_templates = [
        f"You've probably seen {topic} all over your feed. Here's what's actually going on, and why it matters to you.",
        f"Everyone is talking about {topic} right now. Let me break it down in under 20 seconds.",
        f"The story behind {topic} is more interesting than you think. Here's what you need to know."
    ]

    cta_templates = [
        "Follow for more daily updates",
        "Save this for later",
        "Comment your thoughts below",
        "Share this with someone who needs to see it"
    ]

    hook = random.choice(hook_templates)
    script = random.choice(script_templates)
    cta = random.choice(cta_templates)

    clip_names = ', '.join([c['filename'] for c in clips])
    hashtag_string = hashtags if hashtags else f"#{topic.replace(' ', '').lower()}"
    caption = f"{hook} {hashtag_string} #fyp #trending"

    plan = {
        'trend_topic': topic,
        'hook': hook,
        'voiceover_script': f"{hook}. {script} {cta}.",
        'clips': [
            {
                'order': i + 1,
                'filename': c['filename'],
                'file_id': c['file_id'],
                'trim_start': 0,
                'trim_end': 5
            }
            for i, c in enumerate(clips)
        ],
        'caption': caption[:150],
        'hashtags': f"{hashtag_string} #fyp #trending #viral",
        'call_to_action': cta,
        'duration_seconds': len(clips) * 5
    }

    return plan

def save_plan(plan):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Production Plans"
    headers = {
        'Authorization': f'Bearer {AIRTABLE_TOKEN}',
        'Content-Type': 'application/json'
    }
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    plan_id = f"plan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    record = {
        'fields': {
            'Plan ID': plan_id,
            'Trend topic': plan['trend_topic'],
            'Clips used': ', '.join([c['filename'] for c in plan['clips']]),
            'Voiceover script': plan['voiceover_script'],
            'Caption': plan['caption'],
            'Hashtags': plan['hashtags'],
            'Status': 'ready',
            'Created at': now
        }
    }

    response = requests.post(url, json={'records': [record]}, headers=headers)
    print(f"Saved plan: status {response.status_code}")
    if response.status_code != 200:
        print(response.text)
        return None

    saved_id = response.json().get('records', [{}])[0].get('id')
    print(f"Plan saved with ID: {saved_id}")

    with open('production_plan.json', 'w') as f:
        json.dump(plan, f, indent=2)
    print("production_plan.json saved locally")

    return saved_id

if __name__ == '__main__':
    print("Starting production planner...")
    assets = get_assets()
    if not assets:
        print("No assets found — exiting")
        exit(1)

    trend = get_top_trend()
    if not trend:
        print("No trends found — exiting")
        exit(1)

    clips = pick_clips(assets)
    plan = build_plan(trend, clips)

    print(f"\nProduction plan:")
    print(f"  Hook: {plan['hook']}")
    print(f"  Script: {plan['voiceover_script']}")
    print(f"  Clips: {[c['filename'] for c in plan['clips']]}")
    print(f"  Caption: {plan['caption']}")

    save_plan(plan)
    print("\nDone")

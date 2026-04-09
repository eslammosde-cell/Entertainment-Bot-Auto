import os
import asyncio
import json
import edge_tts
import time
import re
import feedparser
import random
from groq import Groq
from datetime import datetime, timezone

# إعداد المفاتيح
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

def get_smart_blog_post():
    """يجلب مقالاً عشوائياً من آخر 50 تدوينة لضمان التنوع وعدم التكرار."""
    rss_url = "https://familytvr.blogspot.com/feeds/posts/default?alt=rss&max-results=50"
    feed = feedparser.parse(rss_url)
    
    if not feed.entries:
        print("❌ RSS Empty")
        return None

    # اختيار مقال عشوائي لضمان تحديث المحتوى دائماً
    entry = random.choice(feed.entries)
    
    # استخراج المحتوى وتنظيفه من الـ HTML
    raw_content = entry.get('content', [{}])[0].get('value', entry.get('summary', ''))
    clean_text = re.sub('<[^<]+?>', '', raw_content)
    
    return {
        "title": entry.title,
        "content": clean_text[:4000],
        "link": entry.link
    }

async def generate_content(blog_data):
    """تحويل محتوى المقال إلى سيناريو فيديو احترافي (English Only)."""
    prompt = f"""
    Role: Professional Tech Journalist.
    Task: Convert this blog article into a viral 4-segment YouTube script.
    Topic: {blog_data['title']}
    Source: {blog_data['content']}
    
    Rules:
    1. Output ONLY JSON with 'stories' and 'metadata'.
    2. Tone: Professional and educational. No dark/mystery themes.
    3. Language: English.
    4. Call to Action: Visit {blog_data['link']} for more details.
    """
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(completion.choices[0].message.content)

def update_rss(data, run_number, blog_link):
    """توليد ملف RSS ببيانات يوتيوب المطلوبة (Email, Owner, Category)."""
    pub_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    audio_url = f"https://github.com/eslamtechautomation-ctrl/TrustMask-Bot-main/releases/download/v{run_number}/episode.mp3"
    cover_url = "https://raw.githubusercontent.com/eslamtechautomation-ctrl/TrustMask-Bot-main/main/podcast_cover.jpg"
    
    meta = data.get('metadata', {})
    actual_title = meta.get('youtube_title', f"Tech Update v{run_number}")
    tags = ", ".join(meta.get('tags', ["Tech", "2026"]))
    
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Family TVR Official Podcast</title>
    <link>https://familytvr.blogspot.com/</link>
    <language>en-us</language>
    <itunes:author>Family TVR</itunes:author>
    <itunes:owner>
      <itunes:name>Family TVR Admin</itunes:name>
      <itunes:email>eslammosde@gmail.com</itunes:email>
    </itunes:owner>
    <itunes:category text="Technology"><itunes:category text="Tech News"/></itunes:category>
    <itunes:image href="{cover_url}"/>
    <item>
      <title><![CDATA[{actual_title}]]></title>
      <description><![CDATA[{meta.get('description', '')}]]></description>
      <pubDate>{pub_date}</pubDate>
      <itunes:keywords>{tags}</itunes:keywords>
      <enclosure url="{audio_url}" length="1048576" type="audio/mpeg"/>
      <guid isPermaLink="false">v{run_number}_{int(time.time())}</guid>
    </item>
  </channel>
</rss>"""
    with open("podcast.xml", "w", encoding="utf-8") as f:
        f.write(rss_content.strip())

async def main():
    print("📡 Fetching blog post...")
    blog_data = get_smart_blog_post()
    if not blog_data: return

    data = await generate_content(blog_data)
    run_num = os.getenv("GITHUB_RUN_NUMBER", "1")
    full_script = "\n\n".join([s.get('content', '') for s in data.get('stories', [])])

    print("🎙️ Generating Audio...")
    communicate = edge_tts.Communicate(full_script, "en-US-ChristopherNeural")
    await communicate.save("episode.mp3")
    
    if os.path.exists("episode.mp3") and os.path.getsize("episode.mp3") > 0:
        update_rss(data, run_num, blog_data['link'])
        print(f"✅ Success! Generated for: {blog_data['title']}")

if __name__ == "__main__":
    asyncio.run(main())

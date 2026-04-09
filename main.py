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

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

def get_smart_blog_post():
    # سحب آخر 50 مقال لضمان التنوع
    rss_url = "https://familytvr.blogspot.com/feeds/posts/default?alt=rss&max-results=50"
    feed = feedparser.parse(rss_url)
    
    if not feed.entries:
        return None

    # اختيار مقال عشوائي
    entry = random.choice(feed.entries)
    
    # التأكد من سحب المحتوى (تجاوز أخطاء KeyError السابقة)
    raw_content = entry.get('content', [{}])[0].get('value', entry.get('summary', ''))
    clean_text = re.sub('<[^<]+?>', '', raw_content)
    
    return {
        "title": entry.title,
        "content": clean_text[:4000],
        "link": entry.link
    }

async def generate_content(blog_data):
    # موجه تقني احترافي يتناسب مع عقلية المطور (Kotlin style clarity)
    prompt = f"""
    Role: Professional Tech Content Creator.
    Task: Convert this article into a viral 4-segment YouTube script.
    Topic: {blog_data['title']}
    Source: {blog_data['content']}
    
    Rules:
    1. Output ONLY JSON.
    2. 4 engaging technical stories (400 words each).
    3. Metadata: YouTube Title, SEO Description, and 20 Tags.
    4. Language: English for US/Europe markets.
    """
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(completion.choices[0].message.content)

def update_rss(data, run_number, blog_link):
    pub_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    audio_url = f"https://github.com/eslamtechautomation-ctrl/TrustMask-Bot-main/releases/download/v{run_number}/episode.mp3"
    cover_url = "https://raw.githubusercontent.com/eslamtechautomation-ctrl/TrustMask-Bot-main/main/podcast_cover.jpg"
    
    meta = data.get('metadata', {})
    actual_title = meta.get('youtube_title', f"Tech Update v{run_number}")
    tags = ", ".join(meta.get('tags', ["Tech", "2026"]))
    
    # إضافة بيانات يوتيوب المطلوبة: الإيميل، المالك، والتصنيف
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Family TVR Tech Podcast</title>
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
    blog_data = get_smart_blog_post()
    if not blog_data: return
    
    data = await generate_content(blog_data)
    run_num = os.getenv("GITHUB_RUN_NUMBER", "1")
    full_script = "\n\n".join([s.get('content', '') for s in data.get('stories', [])])

    # توليد الصوت
    communicate = edge_tts.Communicate(full_script, "en-US-ChristopherNeural")
    await communicate.save("episode.mp3")
    
    if os.path.exists("episode.mp3") and os.path.getsize("episode.mp3") > 0:
        update_rss(data, run_num, blog_data['link'])
        print(f"✅ RSS Updated for: {blog_data['title']}")

if __name__ == "__main__":
    asyncio.run(main())

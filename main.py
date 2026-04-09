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
    rss_url = "https://familytvr.blogspot.com/feeds/posts/default?alt=rss&max-results=50"
    feed = feedparser.parse(rss_url)
    if not feed.entries: return None

    entry = random.choice(feed.entries)
    raw_content = entry.content[0].value if 'content' in entry else entry.summary
    
    # 1. استخراج الروابط (جوجل بلاي أو روابط التحميل)
    links = re.findall(r'href="(http[s]?://[^"]+)"', raw_content)
    app_link = next((l for l in links if 'play.google' in l or 'bit.ly' in l), entry.link)

    # 2. استخراج الهاشتاجات الأصلية من المقال
    original_hashtags = " ".join(re.findall(r'#\w+', raw_content))
    
    clean_text = re.sub('<[^<]+?>', '', raw_content) 

    return {
        "title": entry.title, 
        "content": clean_text[:4000], 
        "link": app_link, 
        "hashtags": original_hashtags
    }

async def generate_content(blog_data):
    # إجبار الذكاء الاصطناعي على استخدام العنوان والوصف الأصلي
    prompt = f"""
    Create a YouTube script in JSON for: {blog_data['title']}
    App Link: {blog_data['link']}
    Original Tags: {blog_data['hashtags']}
    
    Rules:
    - youtube_title must be: {blog_data['title']}
    - description must include the App Link and Original Tags.
    - Create 4 segments for audio.
    """
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(completion.choices[0].message.content)

def update_rss(data, run_number, blog_data):
    timestamp = int(time.time())
    pub_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    audio_url = f"https://github.com/eslamtechautomation-ctrl/TrustMask-Bot-main/releases/download/v{run_number}/episode.mp3"
    
    meta = data.get('metadata', {})
    # استخدام العنوان المستخرج من المقال مباشرة
    actual_title = blog_data['title']
    
    # كتابة الـ RSS بشكل نصي صحيح لتجنب SyntaxError
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Family TVR News</title>
    <item>
      <title><![CDATA[{actual_title}]]></title>
      <description><![CDATA[{meta.get('description', '')}]]></description>
      <pubDate>{pub_date}</pubDate>
      <enclosure url="{audio_url}" length="1048576" type="audio/mpeg"/>
      <guid isPermaLink="false">v{run_number}_{timestamp}</guid>
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
    
    stories = data.get('stories', [])
    full_script = "\n\n".join([s.get('content', '') for s in stories])

    if len(full_script.strip()) > 50:
        communicate = edge_tts.Communicate(full_script, "en-US-ChristopherNeural")
        await communicate.save("episode.mp3")
        
        if os.path.exists("episode.mp3") and os.path.getsize("episode.mp3") > 0:
            update_rss(data, run_num, blog_data)
            print(f"✅ Success: {blog_data['title']}")

if __name__ == "__main__":
    asyncio.run(main())

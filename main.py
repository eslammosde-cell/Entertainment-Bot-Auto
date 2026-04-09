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
    
    if not feed.entries:
        return None

    # منطق الاختيار: نختار مقالاً عشوائياً من آخر 50 مقال لضمان التنوع
    # هذا يضمن أنه حتى لو لم تنشر مقالاً جديداً، سيختار البوت مقالاً سابقاً ويعيد صياغته
    entry = random.choice(feed.entries)
    
    # التأكد من سحب المحتوى بشكل صحيح من بلوجر
    raw_content = entry.get('content', [{}])[0].get('value', entry.get('summary', ''))
    clean_text = re.sub('<[^<]+?>', '', raw_content) # تنظيف HTML
    
    return {
        "title": entry.title,
        "content": clean_text[:4000],
        "link": entry.link
    }

async def generate_content(blog_data):
    # الموجه يركز على المحتوى التقني لمدونتك familytvr.blogspot.com
    prompt = f"""
    Role: Professional Tech Content Creator.
    Task: Convert this blog article into a viral 4-segment YouTube script.
    Topic: {blog_data['title']}
    Source Content: {blog_data['content']}
    
    Instructions:
    1. Tone: Professional, informative, and educational (No dark/mystery themes).
    2. Format: Output ONLY a JSON object.
    3. Promotion: Mention visiting {blog_data['link']} for the full technical guide.
    4. Metadata: Provide a viral 'youtube_title', SEO 'description', and 20 'tags'.
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
    tags_string = ", ".join(meta.get('tags', ["Tech", "Software", "Android"]))
    
    # إضافة البيانات المطلوبة ليوتيوب (الإيميل، المالك، التصنيف)
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Family TVR Tech Insights</title>
    <link>https://familytvr.blogspot.com/</link>
    <language>en-us</language>
    <itunes:author>Family TVR</itunes:author>
    <itunes:owner>
      <itunes:name>Family TVR Admin</itunes:name>
      <itunes:email>eslammosde@gmail.com</itunes:email>
    </itunes:owner>
    <itunes:category text="Technology">
      <itunes:category text="Tech News"/>
    </itunes:category>
    <itunes:image href="{cover_url}"/>
    <description>Latest tech updates, software reviews, and guides from Family TVR.</description>
    <item>
      <title><![CDATA[{actual_title}]]></title>
      <description><![CDATA[{meta.get('description', '')}]]></description>
      <pubDate>{pub_date}</pubDate>
      <itunes:keywords>{tags_string}</itunes:keywords>
      <enclosure url="{audio_url}" length="1048576" type="audio/mpeg"/>
      <guid isPermaLink="false">v{run_number}_{int(time.time())}</guid>
      <itunes:explicit>no</itunes:explicit>
    </item>
  </channel>
</rss>"""
    with open("podcast.xml", "w", encoding="utf-8") as f:
        f.write(rss_content.strip())

async def main():
    print("📡 Fetching blog data...")
    blog_data = get_smart_blog_post()
    if not blog_data: return

    print(f"🤖 Processing: {blog_data['title']}")
    data = await generate_content(blog_data)
    run_num = os.getenv("GITHUB_RUN_NUMBER", "1")
    full_script = "\n\n".join([s.get('content', '') for s in data.get('stories', [])])

    if len(full_script.strip()) > 50:
        print("🎙️ Generating Audio...")
        communicate = edge_tts.Communicate(full_script, "en-US-ChristopherNeural")
        await communicate.save("episode.mp3")
        
        if os.path.exists("episode.mp3") and os.path.getsize("episode.mp3") > 0:
            update_rss(data, run_num, blog_data['link'])
            print(f"✅ RSS & Audio Ready for: {blog_data['title']}")

if __name__ == "__main__":
    asyncio.run(main())

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
    
    # استخراج كافة الروابط الموجودة في المقال قبل تنظيف الـ HTML
    links = re.findall(r'href="(http[s]?://[^"]+)"', raw_content)
    # تصفية الروابط لاستخراج روابط جوجل بلاي أو روابط التحميل فقط
    app_links = [l for l in links if 'play.google' in l or 'bit.ly' in l or 'apk' in l]
    app_link = app_links[0] if app_links else entry.link

    # استخراج الهاشتاجات الموجودة في نص المقال الأصلي
    original_hashtags = re.findall(r'#\w+', raw_content)
    
    clean_text = re.sub('<[^<]+?>', '', raw_content) 

    return {
        "title": entry.title, 
        "content": clean_text[:4000], 
        "link": app_link, # استخدام رابط التطبيق المكتشف
        "original_tags": " ".join(original_hashtags)
    }

async def generate_content(blog_data):
    # إجبار الذكاء الاصطناعي على استخدام بيانات المقال الأصلية
    prompt = f"""
    Role: Professional Tech Video Scriptwriter.
    Original Blog Title: {blog_data['title']}
    Original Hashtags: {blog_data['original_tags']}
    App/Source Link: {blog_data['link']}
    Content Source: {blog_data['content']}
    
    Strict Task:
    1. Use the "Original Blog Title" as the 'youtube_title'.
    2. The 'description' MUST start with a summary of the article, followed by: "Download/Access here: {blog_data['link']}".
    3. Include these original hashtags in the description: {blog_data['original_tags']}.
    4. Create 4 engaging audio segments (English) for the video script.
    5. Output ONLY a valid JSON object.
    """
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(completion.choices[0].message.content)

def update_rss(data, run_number):
    pub_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    audio_url = f"https://github.com/eslamtechautomation-ctrl/TrustMask-Bot-main/releases/download/v{run_number}/episode.mp3"
    cover_url = "https://raw.githubusercontent.com/eslamtechautomation-ctrl/TrustMask-Bot-main/main/podcast_cover.jpg"
    
    meta = data.get('metadata', {})
    # استخدام العنوان المستخرج من المقال
    actual_title = meta.get('youtube_title', f"Tech Update v{run_number}")
    
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Family TVR Official Podcast</title>
    <itunes:owner>
      <itunes:name>Family TVR Admin</itunes:name>
      <itunes:email>eslammosde@gmail.com</itunes:email>
    </itunes:owner>
    <itunes:category text="Technology"/>
    <itunes:image href="{cover_url}"/>
    <language>en-us</language>
    <item>
      <title><![CDATA[{actual_title}]]></title>
      <description><![CDATA[{meta.get('description', '')}]]></description>
      <pubDate>{pub_date}</pubDate>
      <enclosure url="{audio_url}" length="1048576" type="audio/mpeg"/>
      <guid isPermaLink="false">v{run_number}</guid>
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
            update_rss(data, run_num)
            print(f"✅ RSS Updated using original title: {blog_data['title']}")

if __name__ == "__main__":
    asyncio.run(main())

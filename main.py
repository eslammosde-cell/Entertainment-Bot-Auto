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

# إعداد مفتاح Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

def get_smart_blog_post():
    """يجلب مقالاً عشوائياً من آخر 50 تدوينة لضمان التنوع."""
    rss_url = "https://familytvr.blogspot.com/feeds/posts/default?alt=rss&max-results=50"
    feed = feedparser.parse(rss_url)
    
    if not feed.entries:
        print("❌ لا توجد مقالات في الـ RSS")
        return None

    # اختيار مقال عشوائي لضمان محتوى متجدد دائماً حتى لو لم تنشر جديداً
    entry = random.choice(feed.entries)
    
    # استخراج المحتوى وتنظيفه من HTML ليكون جاهزاً للذكاء الاصطناعي
    raw_content = entry.get('content', [{}])[0].get('value', entry.get('summary', ''))
    clean_text = re.sub('<[^<]+?>', '', raw_content)
    
    return {
        "title": entry.title,
        "content": clean_text[:4000],
        "link": entry.link
    }

async def generate_content(blog_data):
    """صياغة سيناريو احترافي ومحتوى وصفي ليوتيوب بناءً على المقال."""
    prompt = f"""
    Role: Professional Tech Video Scriptwriter.
    Topic: {blog_data['title']}
    Source Content: {blog_data['content']}
    
    Instructions:
    1. Output ONLY a JSON object.
    2. Format: 'stories' (4 segments) and 'metadata' (title, description, tags).
    3. Tone: Professional and educational (matching familytvr.blogspot.com).
    4. Language: English (for US/Europe markets).
    5. Promotion: Remind viewers to visit {blog_data['link']} for the full guide.
    """
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(completion.choices[0].message.content)

def update_rss(data, run_number, blog_link):
    """توليد ملف RSS متكامل يلبي كافة شروط يوتيوب بودكاست الرسمية."""
    pub_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    audio_url = f"https://github.com/eslamtechautomation-ctrl/TrustMask-Bot-main/releases/download/v{run_number}/episode.mp3"
    cover_url = "https://raw.githubusercontent.com/eslamtechautomation-ctrl/TrustMask-Bot-main/main/podcast_cover.jpg"
    
    meta = data.get('metadata', {})
    actual_title = meta.get('youtube_title', f"Tech Insights v{run_number}")
    tags_string = ", ".join(meta.get('tags', ["Tech", "Software", "Android"]))
    
    # إضافة وسوم الـ Owner والإيميل والتصنيف كما يطلب يوتيوب
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Family TVR Tech News</title>
    <link>https://familytvr.blogspot.com/</link>
    <language>en-us</language>
    <itunes:author>Family TVR</itunes:author>
    <itunes:owner>
      <itunes:name>Family TVR Team</itunes:name>
      <itunes:email>eslammosde@gmail.com</itunes:email>
    </itunes:owner>
    <itunes:category text="Technology">
      <itunes:category text="Tech News"/>
    </itunes:category>
    <itunes:image href="{cover_url}"/>
    <description>Latest tech updates and guides from Family TVR.</description>
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
    # 1. جلب مقال (عشوائي من الأحدث)
    blog_data = get_smart_blog_post()
    if not blog_data: return

    # 2. توليد المحتوى والوصف التلقائي
    data = await generate_content(blog_data)
    run_num = os.getenv("GITHUB_RUN_NUMBER", "1")
    full_script = "\n\n".join([s.get('content', '') for s in data.get('stories', [])])

    # 3. تحويل النص إلى صوت (Edge TTS)
    if len(full_script.strip()) > 100:
        communicate = edge_tts.Communicate(full_script, "en-US-ChristopherNeural")
        await communicate.save("episode.mp3")
        
        # 4. التحقق من حجم الملف قبل تحديث الـ RSS لتجنب خطأ 422
        if os.path.exists("episode.mp3") and os.path.getsize("episode.mp3") > 0:
            update_rss(data, run_num, blog_data['link'])
            print(f"✅ تم بنجاح! الحلقة: {blog_data['title']}")
        else:
            print("❌ فشل توليد الملف الصوتي (حجمه صفر)")
    else:
        print("❌ السيناريو قصير جداً، تم إلغاء العملية.")

if __name__ == "__main__":
    asyncio.run(main())

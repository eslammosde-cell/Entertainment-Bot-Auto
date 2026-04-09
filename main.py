import os
import asyncio
import json
import edge_tts
import time
import re
import feedparser
from groq import Groq
from datetime import datetime, timezone

# إعداد المفاتيح
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

def get_latest_blog_post():
    rss_url = "https://familytvr.blogspot.com/feeds/posts/default?alt=rss"
    feed = feedparser.parse(rss_url)
    if feed.entries:
        entry = feed.entries[0]
        # التحقق من وجود المحتوى في أكثر من وسم (Blogger Fix)
        raw_content = entry.get('content', [{}])[0].get('value', entry.get('summary', ''))
        clean_text = re.sub('<[^<]+?>', '', raw_content) # تنظيف HTML
        return {"title": entry.title, "content": clean_text[:4000], "link": entry.link}
    return None

async def generate_content(blog_data):
    # الموجه التقني الصافي المعتمد على محتوى المدونة
    prompt = f"""
    Role: Professional Tech Video Scriptwriter.
    Convert this article into a 4-part video script for YouTube/Dailymotion.
    Topic: {blog_data['title']}
    Source: {blog_data['content']}
    
    Instructions:
    1. Professional, educational tone (No mystery/dark themes).
    2. Output ONLY JSON with 'stories' (4 segments) and 'metadata' (title, description, tags).
    3. Include a call to action to visit {blog_data['link']}.
    """
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(completion.choices[0].message.content)

async def main():
    print("📡 Reading from Family TVR RSS...")
    blog_data = get_latest_blog_post()
    if not blog_data: 
        print("❌ RSS Empty"); return

    print(f"🤖 Repurposing: {blog_data['title']}")
    data = await generate_content(blog_data)
    
    run_num = os.getenv("GITHUB_RUN_NUMBER", "1")
    full_script = "\n\n".join([s.get('content', '') for s in data.get('stories', [])])

    # التحقق من وجود نص قبل توليد الصوت لمنع ملفات الصفر بايت
    if len(full_script.strip()) < 10:
        print("❌ Script too short, skipping audio generation."); return

    print("🎙️ Generating Audio...")
    communicate = edge_tts.Communicate(full_script, "en-US-ChristopherNeural")
    await communicate.save("episode.mp3")

    # تأكيد وجود الملف وحجمه قبل إنهاء السكريبت
    if os.path.exists("episode.mp3") and os.path.getsize("episode.mp3") > 0:
        print(f"✅ Success! File size: {os.path.getsize('episode.mp3')} bytes")
        # هنا يتم استدعاء update_rss (تأكد من وجود الوظيفة في الكود لديك)
    else:
        print("❌ Audio generation failed or file is empty.")

if __name__ == "__main__":
    asyncio.run(main())

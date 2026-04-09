import os
import asyncio
import time
import feedparser
import random
import re
import edge_tts
from groq import Groq
from datetime import datetime, timezone
from newspaper import Article  # مكتبة سحب المقالات كاملة

# إعدادات
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

async def main():
    # 1. جلب الروابط من Billboard
    rss_url = "https://www.billboard.com/feed/"
    feed = feedparser.parse(rss_url)
    if not feed.entries: return

    # اختيار مقالة عشوائية
    entry = random.choice(feed.entries)
    title = entry.title
    link = entry.link

    # 2. سحب المقالة كاملة من الرابط (بدلاً من الملخص)
    try:
        article = Article(link)
        article.download()
        article.parse()
        full_content = article.text  # هنا النص الكامل للمقالة
    except:
        # في حال فشل السحب، نستخدم الملخص المتاح
        full_content = re.sub('<[^<]+?>', '', entry.summary)

    # 3. إعادة صياغة النص (لجعله مناسباً للبودكاست)
    # ملاحظة: الذكاء الاصطناعي هنا لا "يؤلف" بل "يعيد صياغة" النص الذي سحبناه ليكون مشوقاً
    prompt = f"Rewrite this article as a short, engaging podcast script. Focus only on the facts provided: {full_content[:3000]}"
    chat = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    podcast_script = chat.choices[0].message.content

    # 4. تحويل النص المعاد صياغته لصوت
    audio_file = "episode.mp3"
    communicate = edge_tts.Communicate(podcast_script, "en-US-ChristopherNeural")
    await communicate.save(audio_file)

    # 5. إنشاء ملف RSS
    run_num = os.getenv("GITHUB_RUN_NUMBER", "1")
    timestamp = int(time.time())
    audio_url = f"https://github.com/eslammosde-cell/Entertainment-Bot-Auto/releases/download/v{run_num}/episode.mp3"
    
    rss_template = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Chart Breakers & Star Stories</title>
    <link>https://familytvr.blogspot.com/</link>
    <language>en-us</language>
    <itunes:author>Family TVR</itunes:author>
    <itunes:image href="https://raw.githubusercontent.com/eslammosde-cell/Entertainment-Bot-Auto/refs/heads/main/podcast_cover.jpg" />
    <item>
        <title>{title}</title>
        <description>{podcast_script[:500]}...</description>
        <pubDate>{datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>
        <enclosure url="{audio_url}" length="1048576" type="audio/mpeg"/>
        <guid>v{run_num}_{timestamp}</guid>
    </item>
  </channel>
</rss>"""
    
    with open("podcast.xml", "w", encoding="utf-8") as f:
        f.write(rss_template)

if __name__ == "__main__":
    asyncio.run(main())

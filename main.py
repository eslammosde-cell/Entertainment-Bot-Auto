import os
import asyncio
import time
import feedparser
import random
import re
import edge_tts
from groq import Groq
from datetime import datetime, timezone

# إعدادات
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

async def main():
    # 1. جلب المقالات من بلوجر
    rss_url = "https://www.billboard.com/feed/"
    feed = feedparser.parse(rss_url)
    if not feed.entries: return

    entry = random.choice(feed.entries)
    title = entry.title
    link = entry.link
    content = re.sub('<[^<]+?>', '', entry.summary)[:1000]

    # 2. توليد وصف ذكي (SEO)
    prompt = f"Create a short YouTube description for: {title}. Include this link: {link}"
    chat = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    description = chat.choices[0].message.content

    # 3. تحويل النص لصوت
    audio_file = "episode.mp3"
    communicate = edge_tts.Communicate(content, "en-US-ChristopherNeural")
    await communicate.save(audio_file)

    # 4. إنشاء ملف RSS (حتى لو حذف يحيا من جديد)
    run_num = os.getenv("GITHUB_RUN_NUMBER", "1")
    timestamp = int(time.time())
    audio_url = f"https://github.com/eslammosde-cell/Entertainment-Bot-Auto/releases/download/v{run_num}/episode.mp3"
    # تأكد أن هذا السطر يبدأ بنفس مستوى المسافات للأسطر السابقة في الكود الخاص بك
   # تأكد أن هذا السطر يبدأ بنفس مستوى المسافات للأسطر السابقة في الكود الخاص بك
    rss_template = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" 
    xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" 
    xmlns:content="http://purl.org/rss/1.0/modules/content/"
    xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <atom:link href="https://eslammosde-cell/Entertainment-Bot-Auto/podcast.xml" rel="self" type="application/rss+xml" />
    <title>Chart Breakers & Star Stories</title>
    <link>https://familytvr.blogspot.com/</link>
    <language>en-us</language>
    <itunes:author>Family TVR</itunes:author>
    <itunes:summary>Did your favorite artist just break a record or a heart? The charts are screaming, and we have the inside story you won't hear anywhere else.</itunes:summary>
    <itunes:owner>
        <itunes:name>Eslam Tech</itunes:name>
        <itunes:email>eslammosde@gmail.com</itunes:email>
    </itunes:owner>
    <itunes:explicit>no</itunes:explicit>
    <itunes:image href="https://raw.githubusercontent.com/eslammosde-cell/Entertainment-Bot-Auto/refs/heads/main/podcast_cover.jpg" />
    <description><![CDATA[Stop guessing with your money. The global economy is changing faster than ever.]]></description>
    <itunes:category text="Business">
        <itunes:category text="Investing"/>
    </itunes:category>
    <item>
        <title>{title}</title>
        <description>{description}</description>
        <pubDate>{datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>
        <enclosure url="{audio_url}" length="1048576" type="audio/mpeg"/>
        <guid>v{run_num}_{timestamp}</guid>
        <itunes:explicit>no</itunes:explicit>
    </item>
</channel>
</rss>"""
    
    with open("podcast.xml", "w", encoding="utf-8") as f:
        f.write(rss_template)

if __name__ == "__main__":
    asyncio.run(main())

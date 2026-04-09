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
    rss_url = "https://www.economist.com/latest/rss.xml"
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
    audio_url = f"https://github.com/eslamtechautomation-ctrl/TrustMask-Bot-main/releases/download/v{run_num}/episode.mp3"
    
    rss_template = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" 
    xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" 
    xmlns:content="http://purl.org/rss/1.0/modules/content/"
    xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <atom:link href="https://github.com/eslamtechautomation-ctrl/TrustMask-Bot-main/blob/main/podcast.xml" rel="self" type="application/rss+xml" />
    <title>The Economic Edge: Master Your Wealth</title>
    <link>https://familytvr.blogspot.com/</link>
    <language>en-us</language>
    <itunes:author>Family TVR</itunes:author>
    <itunes:owner>
        <itunes:name>Eslam Tech</itunes:name>
        <itunes:email>eslammosde@gmail.com</itunes:email>
    </itunes:owner>
    <itunes:image href="https://raw.githubusercontent.com/eslamtechautomation-ctrl/TrustMask-Bot-main/main/assets/podcast_cover.jpg" />
    <description>"Stop guessing with your money. While the world panics, the top 1% are positioning themselves for the biggest wealth transfer in history. Are you with them?"
    The global economy is changing faster than ever. If you aren't staying informed, you're losing value every single day.

This playlist is your ultimate Economic Survival Guide. We go beyond the surface-level news to bring you deep insights, market secrets, and actionable strategies that mainstream media won't tell you. Whether it’s a market crash or a sudden bull run, we help you turn volatility into opportunity.

Inside this Series, we cover:

Market Analysis: Real-time updates on Gold, Stocks, and Global Currencies.

Inflation Protection: Practical steps to keep your savings from disappearing.

Wealth Strategies: How to spot "The Big Trade" before it happens.

Geopolitics & Money: How global conflicts directly impact your bank account.

Don't just watch the news—understand the game. Subscribe and hit the bell icon to stay ahead of the curve.


#EconomyNews #MarketCrash #InvestmentStrategy #FinancialFreedom #GlobalMarkets #WealthProtection #EconomicCrisis2026</description>
    <itunes:category text="Technology" />
    <item>
        <title>{title}</title>
        <description>{description}</description>
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

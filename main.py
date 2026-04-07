import os
import asyncio
import json
import edge_tts
import time
from groq import Groq
from datetime import datetime, timezone

# إعداد المفاتيح
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

async def generate_content():
    trending_topics = """
    1. Cyber Syndicate Secrets: Investigating The Dark Web Groups Targeting Global Remote Workers
    2. Testing a portable solar oven to cook family dinner at the local park
    3. Project Ignition: The Secret Origins Of Free Fire’s Atmospheric Weapon Systems Revealed
    4. Digital Shadows: How Ghost AI Is Impersonating Deceased Users For Profit
    5. The Neural Hijack: Why 2026 Smart Implants Are Compromising Human Privacy Rights
    6. Our family attempts to master professional circus skills in just one weekend challenge
    7. Narrative Analysis: The Rise Of AI Storytelling In Modern Middle Eastern Podcasts
    8. Transforming Our Backyard Into A Sustainable Micro Farm To Feed Six People Daily
    9. The Social Credit Trap: Analyzing 2026 Virtual Reputation Scores In Modern Cities
    10. Why 2026 Quantum Encryption Is Failing To Protect Your Personal Online Banking Data
    11. Building A Fully Functional Underwater Search Drone Using Recycled Household Plastic Waste
    12. Free Fire Lore: The Bioluminescent Mutation Origins Of Kalahari Desert Subsurface Life
    13. Uncertain knowledge and learning uncertainty in ai
    14. Quantifying uncertainty in artificial intelligence
    15. Handling uncertainty in artificial intelligence
    16. Experience and shape ai tools for creativity
    17. Emotional intelligence 2.0
    18. I tested the most futuristic gadgets
    19. New launches smartwatch
    20. Deep Sea Ethics: Protecting Marine Ecosystems
    21. Industrial automation podcast
    22. Semiconductor industry podcast
    23. Wantrepreneur to entrepreneur podcast
    24. Indigenous Data Sovereignty: Protecting Traditional Knowledge
    25. The Algorithmic Forest: Using AI to Restore Biodiversity
    26. Trends that need to stop in 2026
    27. Dances that are trending 2026
    """

    prompt = f"""
    Role: You are a YouTube content creator and a professional expert in search engine optimization for technology news and economics.  
    Task: Produce a complete podcast episode in JSON format only.
    Target Topics List: {trending_topics}
    Rules:
    1. Selection:  the trending topic that is most searched for and relevant to current events..
    2. Format: Output ONLY the JSON object. No extra text.
    3. Stories: 4 unique stories (250-300 words each) with 1-sentence summaries.
    4. Theme: Dark, investigative.
    5. NEVER use the same title twice. 
    6. Create a title and a distinctive, attractive description for each episode based on the story and appropriate tags.
    7. A reminder in the middle of the episode to subscribe to the channel and activate the bell button to follow the episodes and news
    8. A warning in an episode featuring participation on social media sites
    9. Put a question in a circle and a reminder about leaving a comment with an answer
    """
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(completion.choices[0].message.content)

async def text_to_speech(text, output_file):
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    await communicate.save(output_file)

def update_rss(data, run_number):
    pub_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    audio_url = f"https://github.com/eslamtechautomation-ctrl/TrustMask-Bot-main/releases/download/v{run_number}/episode.mp3"
    main_cover_url = "https://raw.githubusercontent.com/eslamtechautomation-ctrl/TrustMask-Bot-main/main/podcast_cover.jpg"
    
    # استخراج العنوان الفعلي من JSON الـ AI
    # لو الـ AI منساش الـ title هياخده، لو نساه هياخد اسم افتراضي برقم الـ Run
    actual_title = data.get('title', f"Tech Mystery Deep Web v{run_number}")
    
    meta = data.get('metadata', {})
    
    # تجميع ملخصات الـ 4 قصص عشان الوصف يتغير كل مرة
    stories = data.get('stories', [])
    chapters = "\n".join([f"- {s.get('summary', 'New tech story update.')}" for s in stories])
    
    full_description = f"{meta.get('description', '')}\n\nWhat's in this episode:\n{chapters}\n\n#2026 #AI #DeepWeb"

    file_size = os.path.getsize("episode.mp3") if os.path.exists("episode.mp3") else "1024"

    # وسم الـ <title> دلوقتي هياخد actual_title المتغير
  # إضافة وسم التصنيف الفرعي ووسوم التحسين
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" 
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" 
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Deep Web Tech Stories: AI &amp; 2026 Trends</title>
    <link>https://familytvr.blogspot.com/</link>
    <description>Investigating the dark side of technology and 2026 innovations.</description>
    <language>en-us</language>
    <itunes:category text="Technology">
      <itunes:category text="Tech News"/>
    </itunes:category>
    <itunes:image href="{main_cover_url}"/>
    <itunes:author>Eslam</itunes:author>
    <itunes:explicit>yes</itunes:explicit>
    <itunes:block>no</itunes:block> 
    <itunes:owner>
      <itunes:name>Eslam</itunes:name>
      <itunes:email>eslammosde@gmail.com</itunes:email>
    </itunes:owner>
    <item>
      <title><![CDATA[{actual_title}]]></title> 
      <description><![CDATA[{full_description}]]></description>
      <content:encoded><![CDATA[{full_description}]]></content:encoded>
      <pubDate>{pub_date}</pubDate>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:episode>{run_number}</itunes:episode>
      <itunes:explicit>yes</itunes:explicit>
      <itunes:image href="{main_cover_url}"/>
      <enclosure url="{audio_url}" length="{file_size}" type="audio/mpeg"/>
      <guid isPermaLink="false">v{run_number}_{int(time.time())}</guid>
    </item>
  </channel>
</rss>"""
    with open("podcast.xml", "w", encoding="utf-8") as f:
        f.write(rss_content.strip())

async def main():
    print("🤖 Generating mystery episode...")
    data = await generate_content()
    
    # التأكد من وجود قصص على الأقل قبل المتابعة
    if not data.get('stories'):
        print("❌ Error: AI returned empty stories. Stopping to prevent corrupted RSS.")
        return

    run_num = os.getenv("GITHUB_RUN_NUMBER", "1")
    
    # تجميع القصص للصوت بأمان (لو الـ content ناقص مش هيطلع Error)
    full_script = "\n\n".join([s.get('content', 'Searching for more deep web data...') for s in data.get('stories', [])])
    
    print(f"🎙️ Creating Audio v{run_num}...")
    await text_to_speech(full_script, "episode.mp3")
    
    print("📝 Writing Fresh RSS Feed...")
    update_rss(data, run_num)
    print(f"✅ Done! Episode v{run_num} is ready.")
if __name__ == "__main__":
    asyncio.run(main())

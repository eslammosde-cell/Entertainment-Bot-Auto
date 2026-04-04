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
    1. Uncertainty in artificial intelligence
    2. Higher dimensions of intelligence
    3. Future innovation ideas
    4. Best ways to make money online 2025
    5. Ecosystemic futures podcast
    6. Why technology is important in our life
    7. Most advanced technology country in the world
    8. Urban Mycelium Networks: Planning Sustainable Smart Cities
    9. The Bio-Digital Divide: How Synthetic Biology Will Redefine Global Trade
    10. Regenerative Finance: Building Economic Systems
    11. Things that are trending in 2026
    12. What is trending in 2026
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
    Role: You are a professional SEO copywriter for tech and deep web news. 
    Task: Produce a complete podcast episode in JSON format only.
    Target Topics List: {trending_topics}
    Rules:
    1. Selection: Pick the MOST relevant trending topic.
    2. Format: Output ONLY the JSON object. No extra text.
    3. Stories: 4 unique stories (250-300 words each) with 1-sentence summaries.
    4. Theme: Dark, investigative, deep web perspective.
    5. NEVER use the same title twice. 
    6. Create a unique, clickbait title for each episode based on the story.
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
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Deep Web Tech Stories: AI &amp; 2026 Trends</title>
    <link>https://familytvr.blogspot.com/</link>
    <description>Investigating the dark side of technology and 2026 innovations.</description>
    <language>en-us</language>
    <itunes:category text="Technology"/>
    <itunes:image href="{main_cover_url}"/>
    <itunes:owner>
      <itunes:name>Eslam</itunes:name>
      <itunes:email>eslammosde@gmail.com</itunes:email>
    </itunes:owner>
    <item>
      <title>{actual_title}</title> 
      <description>{full_description}</description>
      <pubDate>{pub_date}</pubDate>
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

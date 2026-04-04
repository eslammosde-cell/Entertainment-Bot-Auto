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
    # --- [Trending Topics من صور يوتيوب ستوديو - غيرها أسبوعياً] ---
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
    # ------------------------------------------------------------

    prompt = f"""
    Role: You are a professional SEO copywriter for tech and deep web news. 
    Task: Produce a complete podcast episode in JSON format only.

    Target Topics List:
    {trending_topics}

    Rules:
    1. Selection: Pick the MOST relevant trending topic from the list above.
    2. Format: Output ONLY the JSON object. No extra text.
    3. Stories: Provide exactly 4 unique, long-form stories.
       - Each story MUST be between 250 to 300 words.
       - Each story MUST have a 1-sentence 'summary' for SEO timestamps/chapters.
    4. SEO Rule: The "title" and "metadata -> description" MUST start with the selected topic name.
    5. Theme: Dark, investigative, deep web perspective on the selected topic.

    JSON Structure:
    {{
      "title": "Selected Topic - Mysterious Title #hashtags",
      "stories": [
        {{
          "id": 1, 
          "summary": "1-sentence teaser of story 1", 
          "content": "Full 300-word story content..."
        }},
        {{
          "id": 2, 
          "summary": "1-sentence teaser of story 2", 
          "content": "Full 300-word story content..."
        }},
        {{
          "id": 3, 
          "summary": "1-sentence teaser of story 3", 
          "content": "Full 300-word story content..."
        }},
        {{
          "id": 4, 
          "summary": "1-sentence teaser of story 4", 
          "content": "Full 300-word story content..."
        }}
      ],
      "metadata": {{
        "description": "Topic intro + Story summaries + call to action",
        "tags": "list, of, keywords",
        "hashtags": "#2026 #technology #deepweb"
      }}
    }}
    """
    # كمل كود الإرسال للـ AI هنا...
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
    # تاريخ متغير لضمان التحديث الفوري
    pub_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    
    # روابط الملفات
    audio_url = f"https://github.com/eslamtechautomation-ctrl/TrustMask-Bot-main/releases/download/v{run_number}/episode.mp3"
    main_cover_url = "https://github.com/eslamtechautomation-ctrl/TrustMask-Bot-main/blob/f0ee9f1a6dd13bed19bb2f553ff7c200391a0988/podcast_cover.jpg"
    
    # استخراج البيانات من metadata
    meta = data.get('metadata', {})
    full_description = f"{meta.get('description', '')}\n\n🔍 Keywords: {meta.get('tags', '')}\n\n{meta.get('hashtags', '')}"

    # تجهيز عنصر الـ XML الجديد بمسافات صحيحة
    # تأكد أن هذا السطر على نفس مستوى المحاذاة مع الكود الذي قبله
    # تأكد أن هذا السطر على نفس مستوى المحاذاة مع الكود الذي قبله
    unique_version = f"{run_number}_{int(time.time())}"

    new_item = f"""
           <item>
             <title>{data.get('title', 'No Title')} (Ep. v{run_number})</title>
             <description>{full_description}</description>
             <pubDate>{pub_date}</pubDate>
             <itunes:explicit>yes</itunes:explicit>
             <itunes:image href="{main_cover_url}"/>
             <enclosure url="{audio_url}" length="965632" type="audio/mpeg"/>
             <guid isPermaLink="false">v{unique_version}</guid>
           </item>"""

    # قراءة وتحديث ملف RSS
    if not os.path.exists("podcast.xml"):
        # إنشاء ملف بسيط إذا لم يكن موجوداً
        rss_content = '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"><channel><title>Mystery Podcast</title></channel></rss>'
    else:
        with open("podcast.xml", "r", encoding="utf-8") as f:
            rss_content = f.read()

    # إضافة الغلاف إذا لم يوجد
    if "<itunes:image" not in rss_content.split("<item>")[0]:
         rss_content = rss_content.replace("<channel>", f"<channel>\n    <itunes:image href=\"{main_cover_url}\"/>", 1)

    # إضافة الحلقة الجديدة
    if "<item>" in rss_content:
        updated_rss = rss_content.replace("<item>", f"{new_item}\n    <item>", 1)
    else:
        updated_rss = rss_content.replace("</channel>", f"{new_item}\n  </channel>")

    with open("podcast.xml", "w", encoding="utf-8") as f:
        f.write(updated_rss)

async def main():
    print("🤖 Generating mystery episode (4 Stories)...")
    data = await generate_content()
    
    run_num = os.getenv("GITHUB_RUN_NUMBER", "1")
    
    print(f"🎙️ Creating Audio: {data.get('title')}")

    # تجميع الـ 4 قصص معاً
    full_script = "\n\n".join([s['content'] for s in data['stories']])

    await text_to_speech(full_script, "episode.mp3")
    
    print("📝 Updating RSS Feed...")
    update_rss(data, run_num)
    
    print(f"✅ Done! Episode v{run_num} is ready.")

if __name__ == "__main__":
    asyncio.run(main())

import os
import asyncio
import json
import edge_tts
from groq import Groq
from datetime import datetime, timezone

# إعداد المفاتيح
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

async def generate_content():
    # طلب محتوى احترافي مع تشديد على صيغة الـ JSON
    prompt = """
    Role: You are a professional True Crime Scriptwriter. Your task is to output a single, complete podcast episode strictly in JSON format.
    Rules:
    1. Output ONLY the JSON object. 
    2. Language: English.
    3. Stories: 4 unique, long-form stories about 'Romance Scams' and 'Betrayal of Trust'.
    
    JSON Structure:
    {
      "title": "Title #hashtags",
      "stories": [
        {"id": 1, "content": "..."},
        {"id": 2, "content": "..."},
        {"id": 3, "content": "..."},
        {"id": 4, "content": "..."}
      ],
      "metadata": {
        "description": "...",
        "tags": "...",
        "hashtags": "..."
      }
    }
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
    # تاريخ متغير لضمان التحديث الفوري
    pub_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    
    # روابط الملفات
    audio_url = f"https://github.com/eslamelmando76-cmd/MysteryFlow/releases/download/v{run_number}/episode.mp3"
    main_cover_url = "https://raw.githubusercontent.com/eslamelmando76-cmd/TrustMask-Bot/main/podcast_cover.jpg"
    
    # استخراج البيانات من metadata
    meta = data.get('metadata', {})
    full_description = f"{meta.get('description', '')}\n\n🔍 Keywords: {meta.get('tags', '')}\n\n{meta.get('hashtags', '')}\n\nNote: This content is for adults only."

    # تجهيز عنصر الـ XML الجديد بمسافات صحيحة
    new_item = f"""
    <item>
        <title>{data.get('title', 'No Title')} (Ep. v{run_number})</title>
        <description>{full_description}</description>
        <pubDate>{pub_date}</pubDate>
        <itunes:explicit>yes</itunes:explicit>
        <itunes:image href="{main_cover_url}"/>
        <enclosure url="{audio_url}" length="0" type="audio/mpeg"/>
        <guid isPermaLink="false">v{run_number}</guid>
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

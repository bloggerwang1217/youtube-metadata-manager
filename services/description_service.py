"""
Description Generation Service
Generates video descriptions for multiple languages
"""
from typing import Dict


class DescriptionService:
    
    INSTRUMENTAL_TEMPLATES = {
        'zh-Hant': '''
{chinese_introduciton}
–{chinese_name}–
🎵免費樂譜（Gumroad）：https://bloggermandolin.gumroad.com/l/{gumroad_sheetmusic_name}
❤️訂閱Patreon：https://patreon.com/BloggerMandolin
🌟我的串流/社群平台們：https://ffm.bio/bloggermandolin

–更多資料–
曼陀林演奏：Blogger Wang
原曲：{original_song}
伴奏：{instrumental}
樂譜：{musescore_sheetmusic}
中文歌詞翻譯：{chinese_translation}
英文歌詞翻譯：{english_translation}

–聯絡我–
bloggermandolin@proton.me
''',
        'en': '''
{english_introduciton}
–{english_name}–
🎵Free Sheet Music(Gumroad): https://bloggermandolin.gumroad.com/l/{gumroad_sheetmusic_name}
❤️Patreon: https://patreon.com/BloggerMandolin
🌟My Platforms: https://ffm.bio/bloggermandolin

–Info–
Mandolin: Blogger Wang
Original: {original_song}
Instrumental: {instrumental}
Sheet music: {musescore_sheetmusic}
Traditional Chinese translation: {chinese_translation}
English Translation: {english_translation}

–Contact me–
bloggermandolin@proton.me
''',
        'ja': '''
{japanese_introduciton}
–{japanese_name}–
🎵無料楽譜（Gumroad）：https://bloggermandolin.gumroad.com/l/{gumroad_sheetmusic_name}
❤️Patreon：https://patreon.com/BloggerMandolin
🌟プラットフォーム：https://ffm.bio/bloggermandolin

–インフォ–
マンドリン：Blogger Wang
本家様：{original_song}
インスト：{instrumental}
楽譜：{musescore_sheetmusic}
中国語翻訳：{chinese_translation}
英語翻訳：{english_translation}

–Eメール–
bloggermandolin@proton.me
'''
    }
    
    PIANO_TEMPLATES = {
        'zh-Hant': '''
{chinese_introduciton}
–{chinese_name}–
🎵免費樂譜（Gumroad）：https://bloggermandolin.gumroad.com/l/{gumroad_sheetmusic_name}
❤️訂閱Patreon：https://patreon.com/BloggerMandolin
🌟我的串流/社群平台們：https://ffm.bio/bloggermandolin

–更多資料–
曼陀林演奏：Blogger Wang
原曲：{original_song}
樂譜：{musescore_sheetmusic}
鋼琴樂譜參考：{instrumental}
中文歌詞翻譯：{chinese_translation}
英文歌詞翻譯：{english_translation}

–聯絡我–
bloggermandolin@proton.me
''',
        'en': '''
{english_introduciton}
–{english_name}–
🎵Free Sheet Music(Gumroad): https://bloggermandolin.gumroad.com/l/{gumroad_sheetmusic_name}
❤️Patreon: https://patreon.com/BloggerMandolin
🌟My Platforms: https://ffm.bio/bloggermandolin

–Info–
Mandolin: Blogger Wang
Original: {original_song}
Sheet music: {musescore_sheetmusic}
Piano sheet music: {instrumental}
Traditional Chinese translation: {chinese_translation}
English Translation: {english_translation}

–Contact me–
bloggermandolin@proton.me
''',
        'ja': '''
{japanese_introduciton}
–{japanese_name}–
🎵無料楽譜（Gumroad）：https://bloggermandolin.gumroad.com/l/{gumroad_sheetmusic_name}
❤️Patreon：https://patreon.com/BloggerMandolin
🌟プラットフォーム：https://ffm.bio/bloggermandolin

–インフォ–
マンドリン：Blogger Wang
本家様：{original_song}
楽譜：{musescore_sheetmusic}
ピアノ楽譜参考：{instrumental}
中国語翻訳：{chinese_translation}
英語翻訳：{english_translation}

–Eメール–
bloggermandolin@proton.me
'''
    }
    
    @classmethod
    def generate(cls, info_dict: Dict, inst_type: str, language: str = 'en') -> str:
        """Generate description based on template and language"""
        if inst_type == "instrumental" or inst_type == "Inst":
            templates = cls.INSTRUMENTAL_TEMPLATES
        else:  # piano
            templates = cls.PIANO_TEMPLATES
        
        template = templates.get(language, templates['en'])
        
        description = template.format(
            original_song=info_dict.get("original_song", ""),
            chinese_translation=info_dict.get("chinese_translation", ""),
            english_translation=info_dict.get("english_translation", ""),
            instrumental=info_dict.get("instrumental", ""),
            japanese_name=info_dict.get("japanese_name", ""),
            chinese_name=info_dict.get("chinese_name", ""),
            english_name=info_dict.get("english_name", ""),
            musescore_sheetmusic=info_dict.get("musescore_sheetmusic", ""),
            gumroad_sheetmusic_name=info_dict.get("gumroad_sheetmusic_name", ""),
            japanese_introduciton=info_dict.get("japanese_introduction", ""),
            chinese_introduciton=info_dict.get("chinese_introduction", ""),
            english_introduciton=info_dict.get("english_introduction", "")
        )
        
        return description
    
    @staticmethod
    def prepare_info_dict(video_data: Dict) -> Dict:
        """Prepare information dictionary from database data"""
        return {
            "japanese_introduction": (video_data.get("JaDescription") or "") + '\n',
            "chinese_introduction": (video_data.get("ZhHantDescription") or "") + '\n',
            "english_introduction": (video_data.get("EnDescription") or "") + '\n',
            "musescore_sheetmusic": video_data.get("Sheet") or "",
            "gumroad_sheetmusic_name": video_data.get("GumroadSheet") or "",
            "original_song": video_data.get("MV") or "",
            "chinese_translation": video_data.get("ZhHantSubSource") or "",
            "english_translation": video_data.get("EnSubSource") or "",
            "instrumental": video_data.get("Instrumental") or "",
            "japanese_name": video_data.get("JaName") or "",
            "chinese_name": video_data.get("ZhHantName") or "",
            "english_name": video_data.get("EnName") or ""
        }

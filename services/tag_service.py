"""
Tag Management Service
Handles tag grabbing and replacement from reference videos
"""
import os
import csv
import requests
from typing import Optional, List, Dict


class TagService:
    def __init__(self, api_key: str, replacement_csv_path: str):
        self.api_key = api_key
        self.replacement_csv_path = replacement_csv_path
        self.replacement_dict = self._load_replacement_dict()
    
    def _load_replacement_dict(self) -> Dict[str, str]:
        """Load tag replacement dictionary from CSV"""
        replacement_dict = {}
        if os.path.exists(self.replacement_csv_path):
            with open(self.replacement_csv_path, newline='') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if len(row) >= 2:
                        key, value = row[0], row[1]
                        replacement_dict[key] = value
        return replacement_dict
    
    def get_video_tags(self, video_id: str) -> Optional[List[str]]:
        """Get tags from a YouTube video"""
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={self.api_key}"
        response = requests.get(url)
        data = response.json()
        
        if "items" in data and len(data["items"]) > 0:
            tags = data["items"][0]["snippet"].get("tags", [])
            return tags
        
        return None
    
    def replace_tags(self, tags: List[str]) -> List[str]:
        """Replace tag words based on replacement dictionary"""
        replaced_tags = []
        for tag in tags:
            replaced_tag = tag
            for word, replacement in self.replacement_dict.items():
                if word in replaced_tag:
                    replaced_tag = replaced_tag.replace(word, replacement)
            replaced_tags.append(replaced_tag)
        return replaced_tags
    
    def grab_tags(self, reference_video_link: str) -> Optional[str]:
        """Grab and replace tags from a reference video"""
        video_id = self._extract_video_id(reference_video_link)
        tags = self.get_video_tags(video_id)
        
        if tags:
            replaced_tags = self.replace_tags(tags)
            tag_string = ",".join(replaced_tags)
            return tag_string
        
        return None
    
    @staticmethod
    def _extract_video_id(video_link: str) -> str:
        """Extract YouTube video ID from URL"""
        if "youtu.be" in video_link:
            return video_link.split("/")[-1].split("?")[0]
        else:
            return video_link.split("=")[-1].split("&")[0]

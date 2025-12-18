import json
import os
from typing import Dict

class LanguageManager:
    def __init__(self, lang_dir="lang"):
        self.lang_dir = lang_dir
        self.languages = {}
        self.load_languages()
    
    def load_languages(self):
        """Load all language files from lang directory"""
        if not os.path.exists(self.lang_dir):
            os.makedirs(self.lang_dir)
            return
        
        for filename in os.listdir(self.lang_dir):
            if filename.endswith('.json'):
                lang_code = filename.replace('.json', '')
                filepath = os.path.join(self.lang_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.languages[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Error loading language file {filename}: {e}")
    
    def get_text(self, lang_code: str, key: str, **kwargs) -> str:
        """Get translated text by key"""
        # Default to Uzbek if language not found
        if lang_code not in self.languages:
            lang_code = 'uz'
        
        # Get text from language file
        text = self.languages.get(lang_code, {}).get(key, key)
        
        # Format with kwargs if provided
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        
        return text
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get list of available languages"""
        return {
            'uz': '🇺🇿 O\'zbek',
            'en': '🇬🇧 English',
            'ru': '🇷🇺 Русский'
        }

# Global instance
lang_manager = LanguageManager()

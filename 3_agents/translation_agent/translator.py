from deep_translator import GoogleTranslator

class TranslationAgent:
    def __init__(self):
        # We use Google Translate (Auto-detect -> English)
        self.translator = GoogleTranslator(source='auto', target='en')

    def translate(self, text):
        try:
            # 1. Translate
            translated = self.translator.translate(text)
            
            # 2. Check if translation actually happened
            # (If input was "Hello", output is "Hello" -> No translation)
            is_translated = translated.strip().lower() != text.strip().lower()
            
            return {
                "original_text": text,
                "translated_text": translated,
                "is_translated": is_translated,
                "src_lang": "Detected" if is_translated else "English"
            }
        except Exception as e:
            print(f"Translation Failed: {e}")
            return {
                "original_text": text,
                "translated_text": text, # Fallback to original
                "is_translated": False,
                "src_lang": "Error"
            }

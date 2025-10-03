"""
Text Normalization for Hawaiian Song Titles and Composer Names
Handles ʻokina, macrons, and common variations for accurate matching
"""

import re
import unicodedata


class HawaiianTextNormalizer:
    """Normalize Hawaiian text for consistent matching"""
    
    def __init__(self):
        # Diacritic mappings
        self.diacritic_map = {
            'ā': 'a', 'ē': 'e', 'ī': 'i', 'ō': 'o', 'ū': 'u',
            'Ā': 'A', 'Ē': 'E', 'Ī': 'I', 'Ō': 'O', 'Ū': 'U'
        }
        
        # ʻOkina variations (many old books don't have proper ʻokina)
        self.okina_variants = [
            'ʻ',    # Proper ʻokina (U+02BB)
            ''',    # Right single quotation mark (U+2019)
            ''',    # Left single quotation mark (U+2018)
            '`',    # Grave accent
            "'",    # Straight apostrophe
            ''      # Sometimes just omitted
        ]
        
        # Common word variations in Hawaiian
        self.word_variations = {
            'ke': ['ka'],
            'ka': ['ke'],
            'o': ['of'],
            'of': ['o'],
            'me': ['and', 'with'],
            'and': ['me'],
            'with': ['me']
        }
        
        # Common composer name variations
        self.composer_variations = {
            'chas': ['charles', 'charlie'],
            'charles': ['chas', 'charlie', 'c.'],
            'charlie': ['charles', 'chas'],
            'e.': ['edward'],
            'edward': ['e.'],
            'w.': ['william'],
            'william': ['w.', 'will'],
            'j.': ['john'],
            'john': ['j.'],
            'king': ['chas e. king', 'charles e. king', 'c. e. king']
        }
    
    def normalize_diacritics(self, text):
        """Remove Hawaiian diacritics for matching"""
        if not text:
            return ""
        
        # Replace mapped diacritics
        for accented, plain in self.diacritic_map.items():
            text = text.replace(accented, plain)
        
        # Use Unicode normalization as backup
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        
        return text
    
    def normalize_okina(self, text):
        """Standardize ʻokina variants"""
        if not text:
            return ""
        
        # Replace all ʻokina variants with empty string for matching
        for variant in self.okina_variants:
            text = text.replace(variant, '')
        
        return text
    
    def normalize_spacing_punctuation(self, text):
        """Standardize spacing and punctuation"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common punctuation that varies between sources
        text = re.sub(r'[,.:;!?\-\(\)\[\]\""]', '', text)
        
        # Remove leading/trailing spaces
        text = text.strip()
        
        return text
    
    def normalize_case(self, text):
        """Convert to lowercase for matching"""
        return text.lower() if text else ""
    
    def normalize_text(self, text):
        """Apply full normalization pipeline"""
        if not text:
            return ""
        
        # Apply all normalizations
        text = self.normalize_diacritics(text)
        text = self.normalize_okina(text)
        text = self.normalize_spacing_punctuation(text)
        text = self.normalize_case(text)
        
        return text
    
    def normalize_composer_name(self, name):
        """Special normalization for composer names"""
        if not name:
            return ""
        
        # Basic normalization
        normalized = self.normalize_text(name)
        
        # Handle common abbreviations and variations
        words = normalized.split()
        expanded_words = []
        
        for word in words:
            if word in self.composer_variations:
                # Use the first (most common) variation
                expanded_words.append(self.composer_variations[word][0])
            else:
                expanded_words.append(word)
        
        return ' '.join(expanded_words)
    
    def get_search_variants(self, text):
        """Generate text variations for fuzzy searching"""
        if not text:
            return []
        
        variants = set()
        
        # Original text
        variants.add(text)
        
        # Normalized version
        normalized = self.normalize_text(text)
        variants.add(normalized)
        
        # With/without ʻokina
        for okina_variant in self.okina_variants[:3]:  # Use common ones
            variant = text.replace('ʻ', okina_variant)
            variants.add(self.normalize_text(variant))
        
        # With/without diacritics
        no_diacritics = self.normalize_diacritics(text)
        variants.add(self.normalize_text(no_diacritics))
        
        # Remove empty strings and duplicates
        return [v for v in variants if v]


# Global normalizer instance
normalizer = HawaiianTextNormalizer()


def normalize_title(title):
    """Convenience function for title normalization"""
    return normalizer.normalize_text(title)


def normalize_composer(composer):
    """Convenience function for composer normalization"""
    return normalizer.normalize_composer_name(composer)


def get_title_variants(title):
    """Convenience function to get title search variants"""
    return normalizer.get_search_variants(title)


if __name__ == "__main__":
    # Test the normalization
    test_cases = [
        "Aloha ʻOe",
        "Pua ʻAhihi",
        "Nā Lei O Hawaiʻi", 
        "Ka Makani Kaʻili Aloha",
        "Chas E. King",
        "Charles E. King",
        "Queen Liliʻuokalani"
    ]
    
    print("Text Normalization Test:")
    print("=" * 50)
    
    for text in test_cases:
        normalized = normalize_title(text)
        composer_norm = normalize_composer(text)
        variants = get_title_variants(text)
        
        print(f"Original: {text}")
        print(f"Title norm: {normalized}")
        print(f"Composer norm: {composer_norm}")
        print(f"Variants: {variants[:3]}...")  # Show first 3
        print("-" * 30)
from typing import Dict

class ComplexityAnalyzer:
    def __init__(self):
        self.legal_jargon = [
            'whereas', 'herein', 'thereof', 'heretofore', 'aforementioned', 
            'pursuant', 'notwithstanding', 'hereby', 'herewith'
        ]

    def analyze_complexity(self, content: str) -> Dict:
        """Calculate document complexity metrics"""
        sentences = content.split('.')
        words = content.split()
        
        if not words:
            return {"complexity_score": 0.0, "readability_score": 0.0}
        
        avg_sentence_length = len(words) / max(len(sentences), 1)
        unique_words = len(set(word.lower().strip('.,!?";:()[]') for word in words))
        vocabulary_richness = unique_words / len(words) if words else 0
        
        legal_jargon_count = sum(1 for word in self.legal_jargon if word in content.lower())
        
        complexity_score = min(
            (avg_sentence_length / 20) * 0.4 +
            vocabulary_richness * 0.3 +
            (legal_jargon_count / 10) * 0.3,
            1.0
        )
        
        return {
            "complexity_score": round(complexity_score, 3),
            "avg_sentence_length": round(avg_sentence_length, 2),
            "vocabulary_richness": round(vocabulary_richness, 3),
            "legal_jargon_count": legal_jargon_count,
            "total_words": len(words),
            "total_sentences": len(sentences)
        }
from __future__ import annotations

from src.core.models import ListingCandidate


def _phash_safe(image_path: str):
    try:
        from PIL import Image
        import imagehash

        return imagehash.phash(Image.open(image_path))
    except Exception:
        return None


def score_candidates(image_path: str, candidates: list[ListingCandidate], query_hint: str) -> list[ListingCandidate]:
    src_hash = _phash_safe(image_path)
    hint_tokens = set(query_hint.lower().split())
    for c in candidates:
        title_tokens = set(c.title.lower().split())
        token_hit = len(hint_tokens.intersection(title_tokens)) if hint_tokens else 0

        # Class 1/2/3 approximation signals (MVP fallback without heavy models)
        image_signal = 25.0 if (src_hash is not None and c.image_url) else 10.0
        text_signal = min(45.0, token_hit * 12.0)
        social_signal = min(20.0, (c.review_count or 0) * 0.2)
        score = max(0.0, min(100.0, image_signal + text_signal + social_signal + 20.0))

        c.similarity_score = round(score, 2)
        if score >= 85:
            c.class_label = "class_1"
            c.reason = "이미지/텍스트 신호가 매우 강함"
        elif score >= 70:
            c.class_label = "class_2"
            c.reason = "텍스트/옵션 유사도 중심으로 동일제품 가능성 높음"
        else:
            c.class_label = "class_3"
            c.reason = "추론상 유사 후보"
    return sorted(candidates, key=lambda x: x.similarity_score, reverse=True)

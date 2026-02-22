from __future__ import annotations

import re

from src.core.models import ListingCandidate, VerifyResult


_SIZE_RE = re.compile(r"(\d+(?:\.\d+)?\s?(?:ml|l|g|kg|mm|cm|m|개|입))", re.IGNORECASE)


def _extract_size_tokens(text: str) -> set[str]:
    return {m.group(1).lower().replace(" ", "") for m in _SIZE_RE.finditer(text or "")}


def verify_candidate(candidate: ListingCandidate, query_hint: str) -> VerifyResult:
    fail_reasons: list[str] = []
    checks: list[str] = []
    score = candidate.similarity_score
    title_l = candidate.title.lower()
    hint_tokens = [t for t in query_hint.lower().split() if t]

    checks.append("1:image_similarity=" + ("pass" if score >= 60 else "fail"))
    if score < 60:
        fail_reasons.append("대표이미지 유사도 낮음")

    token_hit = any(t in title_l for t in hint_tokens) if hint_tokens else True
    checks.append("2:title_token=" + ("pass" if token_hit else "fail"))
    if not token_hit:
        fail_reasons.append("핵심 토큰 불일치")

    size_hit = bool(_extract_size_tokens(candidate.title) & _extract_size_tokens(query_hint)) if query_hint else True
    checks.append("3:spec_size=" + ("pass" if size_hit else "warn"))

    material_words = ["cotton", "면", "steel", "스틸", "가죽", "leather", "플라스틱"]
    material_hint = [w for w in material_words if w in (query_hint or "").lower()]
    material_match = (not material_hint) or any(w in title_l for w in material_hint)
    checks.append("4:material=" + ("pass" if material_match else "warn"))

    set_words = ["세트", "set", "1개", "2개", "10개"]
    set_hint = [w for w in set_words if w in (query_hint or "").lower()]
    set_match = (not set_hint) or any(w in title_l for w in set_hint)
    checks.append("5:set_count=" + ("pass" if set_match else "warn"))

    color_words = ["black", "white", "red", "blue", "블랙", "화이트", "레드", "블루"]
    color_hint = [w for w in color_words if w in (query_hint or "").lower()]
    color_match = (not color_hint) or any(w in title_l for w in color_hint)
    checks.append("6:color_option=" + ("pass" if color_match else "warn"))

    checks.append("7:ocr_logo_model=skip")

    price_ok = not (candidate.price and candidate.price > 3 * 10000)
    checks.append("8:price_outlier=" + ("pass" if price_ok else "fail"))
    if not price_ok:
        fail_reasons.append("가격대 이상치 경고")

    checks.append("9:review_signal=" + ("pass" if (candidate.review_count or 0) > 0 else "warn"))
    checks.append("10:category_match=warn")

    confidence = max(0.0, min(100.0, score - len(fail_reasons) * 8 + (3 if token_hit else 0)))
    verified = confidence >= 65
    summary = "; ".join([
        f"class={candidate.class_label}",
        f"score={candidate.similarity_score}",
        f"fails={len(fail_reasons)}",
        "checks=" + ",".join(checks),
    ])
    return VerifyResult(verified_flag=verified, confidence=round(confidence, 2), fail_reasons=fail_reasons, compare_summary=summary)

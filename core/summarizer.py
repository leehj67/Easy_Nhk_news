# -*- coding: utf-8 -*-
"""기사 추출 요약 (extractive, LLM 없음)"""
from typing import List

from .tokenizer import split_sentences


def extract_summary(body_text: str, max_bullets: int = 3) -> List[str]:
    """
    일본어 기사 본문에서 핵심 문장 추출.
    - 첫 문장 (도입)
    - 키워드 포함 문장 (중간)
    - 결론성 문장 (마지막 근처)
    중복·짧은 문장 제외.
    """
    if not body_text or not body_text.strip():
        return []
    sentences = split_sentences(body_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) >= 20]
    if not sentences:
        return []
    # 날짜/숫자만 있는 문장 제외
    filtered = []
    for s in sentences:
        if s.isdigit() or (len(s) < 15 and any(c in s for c in "年月日")):
            continue
        filtered.append(s)
    if not filtered:
        return [sentences[0][:150] + ("…" if len(sentences[0]) > 150 else "")] if sentences else []
    # 첫 문장
    result = [filtered[0][:120] + ("…" if len(filtered[0]) > 120 else "")]
    if len(filtered) == 1:
        return result
    # 중간: 2번째~끝-1 중 가장 긴 문장 (핵심 포인트일 가능성)
    mid = filtered[1:-1] if len(filtered) > 2 else filtered[1:]
    if mid:
        mid_sorted = sorted(mid, key=len, reverse=True)
        for cand in mid_sorted[:2]:
            if cand not in result and len(cand) >= 25:
                result.append(cand[:120] + ("…" if len(cand) > 120 else ""))
                if len(result) >= max_bullets:
                    break
    # 결론: 마지막 문장
    if len(filtered) > 1 and len(result) < max_bullets:
        last = filtered[-1]
        if last not in result:
            result.append(last[:120] + ("…" if len(last) > 120 else ""))
    return result[:max_bullets]

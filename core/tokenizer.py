# -*- coding: utf-8 -*-
"""문장 분리, 단어 추출, 형태소 분석"""
import re
from typing import Dict, List

_tagger = None

# 조사, 조동사, 기호, 접속사, 기능어 제거
_STOP_POS1 = frozenset({
    "助詞", "助動詞", "補助記号", "記号", "接続詞", "感動詞",
    "空白", "フィラー", "非言語音",
})
_STOP_POS2 = frozenset({"接頭辞", "接尾辞"})
_CONTENT_POS1 = frozenset({"名詞", "動詞", "形容詞", "副詞", "形状詞"})
_NUMERIC_SUFFIXES = frozenset({
    "年", "月", "日", "人", "万", "個", "円", "時", "分", "秒",
    "歳", "台", "回", "度", "前", "後", "週", "か月", "ヶ月",
})
_BANNED_LEMMAS = frozenset({
    "の", "が", "を", "に", "は", "で", "も", "へ", "と",
    "て", "た", "だ", "です", "ます", "する", "いる", "ある",
})
_NOUNISH_SUFFIX_SURFACES = frozenset({
    "庁", "県", "市", "町", "村", "所", "駅", "場", "家",
})


def _get_tagger():
    global _tagger
    if _tagger is None:
        from fugashi import Tagger
        _tagger = Tagger()
    return _tagger


def split_sentences(text: str) -> List[str]:
    """문장 단위로 분리"""
    text = text.replace("\n", " ")
    return [p.strip() for p in re.split(r"(?<=[。！？])\s*", text) if p.strip()]


def _token_to_dict(w) -> Dict:
    """fugashi 토큰을 표준 dict로 변환"""
    f = w.feature
    lemma = getattr(f, "lemma", None) or w.surface
    reading = getattr(f, "kana", None) or getattr(f, "lForm", None) or ""
    pos = w.pos or ""
    pos1 = getattr(f, "pos1", None) or (pos.split(",")[0] if pos else "")
    pos2 = getattr(f, "pos2", None) or ""
    return {
        "surface": w.surface,
        "lemma": lemma,
        "reading": reading,
        "pos": pos,
        "pos1": pos1,
        "pos2": pos2,
    }


def _normalize_lemma(tok: Dict) -> Dict:
    """fugashi/unidic 활용형 파편 후처리"""
    surface = tok.get("surface", "")
    lemma = tok.get("lemma", "") or surface
    pos1 = tok.get("pos1", "")
    if pos1 in {"動詞", "形容詞"}:
        if len(lemma) <= 1:
            tok["lemma"] = surface
        elif re.fullmatch(r"[ぁ-ん]+", lemma) and len(lemma) <= 2:
            tok["lemma"] = surface
    return tok


def is_stop_token(tok: Dict) -> bool:
    """조사, 조동사, 기호, 활용형 파편 제거"""
    pos1 = tok.get("pos1", "")
    pos2 = tok.get("pos2", "")
    surface = tok.get("surface", "")
    lemma = tok.get("lemma", "")

    if pos1 in _STOP_POS1:
        return True
    if pos1 == "接尾辞":
        if surface in _NUMERIC_SUFFIXES:
            return False
        if surface in _NOUNISH_SUFFIX_SURFACES:
            return False
        if pos2 and "名詞" in str(pos2):
            return False
        return True
    if pos1 == "名詞" and pos2 == "数詞" and surface.isdigit():
        return False
    if lemma in _BANNED_LEMMAS or surface in _BANNED_LEMMAS:
        return True
    if len(surface) < 2 and not surface.isdigit():
        return True
    if re.fullmatch(r"[ぁ-ん]+", surface):
        if surface.endswith("っ") or len(surface) <= 2:
            return True
        if re.fullmatch(r"[ぁ-ん]{2,3}", lemma):
            return True
    if pos1 in {"動詞", "形容詞"} and len(lemma) <= 1:
        return True
    return False


def merge_numeric_expressions(tokens: List[Dict]) -> List[Dict]:
    """숫자+접미사 결합: 15年前, 2011年3月11日"""
    result = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        surface = t["surface"]
        pos1 = t.get("pos1", "")
        if pos1 == "名詞" and surface.isdigit():
            combined = surface
            j = i + 1
            while j < len(tokens):
                next_t = tokens[j]
                next_surf = next_t["surface"]
                next_pos2 = str(next_t.get("pos2", ""))
                if next_surf in _NUMERIC_SUFFIXES or "助数詞" in next_pos2:
                    combined += next_surf
                    j += 1
                    if next_surf == "前":
                        break
                elif next_surf.isdigit() and len(next_surf) <= 4:
                    if any(x in combined for x in ("年", "月", "万")):
                        combined += next_surf
                        j += 1
                    else:
                        break
                else:
                    break
            result.append({
                "surface": combined,
                "lemma": combined,
                "reading": t.get("reading", ""),
                "pos": t.get("pos", ""),
                "pos1": "名詞",
                "pos2": "数詞",
            })
            i = j
            continue
        result.append(t)
        i += 1
    return result


def _is_numeric_or_date_expr(surface: str) -> bool:
    """날짜/수량 표현 여부"""
    if not surface:
        return False
    if surface.isdigit():
        return True
    return any(c in surface for c in "年月日人万") or (
        surface[-1] in _NUMERIC_SUFFIXES and any(s.isdigit() for s in surface)
    )


def merge_compound_nouns(tokens: List[Dict]) -> List[Dict]:
    """연속 명사 복합명사 결합: 東日本大震災, 警察庁"""
    result = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        pos1 = t.get("pos1", "")
        pos2 = str(t.get("pos2", ""))
        is_noun_like = pos1 == "名詞" or (pos1 == "接尾辞" and "名詞" in pos2)
        if is_noun_like and not _is_numeric_or_date_expr(t["surface"]):
            combined_surf = t["surface"]
            j = i + 1
            while j < len(tokens):
                next_t = tokens[j]
                if _is_numeric_or_date_expr(next_t["surface"]):
                    break
                next_pos1 = next_t.get("pos1", "")
                next_pos2 = str(next_t.get("pos2", ""))
                next_noun_like = next_pos1 == "名詞" or (next_pos1 == "接尾辞" and "名詞" in next_pos2)
                if next_noun_like:
                    combined_surf += next_t["surface"]
                    j += 1
                elif next_pos1 == "接頭辞" and j + 1 < len(tokens):
                    nn = tokens[j + 1]
                    if nn.get("pos1") == "名詞":
                        combined_surf += next_t["surface"] + nn["surface"]
                        j += 2
                    else:
                        break
                else:
                    break
            result.append({
                "surface": combined_surf,
                "lemma": combined_surf,
                "reading": t.get("reading", ""),
                "pos": t.get("pos", ""),
                "pos1": "名詞",
                "pos2": t.get("pos2", ""),
            })
            i = j
            continue
        if is_noun_like and _is_numeric_or_date_expr(t["surface"]):
            result.append(t)
            i += 1
            continue
        if pos1 == "接頭辞" and i + 1 < len(tokens):
            next_t = tokens[i + 1]
            next_pos1 = next_t.get("pos1", "")
            if next_pos1 == "名詞":
                result.append({
                    "surface": t["surface"] + next_t["surface"],
                    "lemma": t["surface"] + next_t["surface"],
                    "reading": next_t.get("reading", ""),
                    "pos": next_t.get("pos", ""),
                    "pos1": "名詞",
                    "pos2": next_t.get("pos2", ""),
                })
                i += 2
                continue
        result.append(t)
        i += 1
    return result


def get_sentence_tokens(sentence: str) -> List[Dict]:
    """문장의 모든 토큰 (surface, lemma) - 본문 하이라이트용"""
    tagger = _get_tagger()
    return [_normalize_lemma(_token_to_dict(w)) for w in tagger(sentence)]


def extract_core_words(sentence: str) -> List[Dict]:
    """학습용 핵심 단어 추출 (품사/중복 필터 적용, 개수 제한 없음)"""
    tagger = _get_tagger()
    raw_tokens = [_normalize_lemma(_token_to_dict(w)) for w in tagger(sentence)]
    merged = merge_numeric_expressions(raw_tokens)
    merged = merge_compound_nouns(merged)
    filtered = [t for t in merged if not is_stop_token(t) and t["pos1"] in _CONTENT_POS1]

    semantic_words = []
    numeric_words = []
    seen_lemma = set()

    for t in filtered:
        lemma = t.get("lemma") or t["surface"]
        surface = t["surface"]
        if lemma in seen_lemma:
            continue
        if len(lemma) < 2:
            continue
        if surface.isdigit() and len(surface) <= 4:
            continue

        seen_lemma.add(lemma)
        word_obj = {
            "surface": t["surface"],
            "lemma": lemma,
            "reading": t.get("reading", ""),
            "pos": t.get("pos", ""),
            "meaning": None,
        }
        if _is_numeric_or_date_expr(surface):
            numeric_words.append(word_obj)
        else:
            semantic_words.append(word_obj)

    return semantic_words + numeric_words


def get_word_info_from_dict(wd: Dict) -> tuple:
    """단어 dict에서 읽기/품사 반환"""
    return wd.get("reading", ""), (wd.get("pos", "") or "").split(",")[0]

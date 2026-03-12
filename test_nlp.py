# -*- coding: utf-8 -*-
"""형태소 분석 및 번역 테스트"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

from janome.tokenizer import Tokenizer
from deep_translator import GoogleTranslator

# Janome
t = Tokenizer()
s = "今日は良い天気です"
tokens = list(t.tokenize(s))
print("Janome OK, tokens:", len(tokens))

# Translation
tr = GoogleTranslator(source="ja", target="ko")
ko = tr.translate(s)
print("Translation OK:", ko)

# JMDict (first run may download ~11MB)
try:
    from jmdictpy import JMDict
    jmd = JMDict(language="eng", auto_update=False)
    r = jmd.lookup("食べる")
    if r and r.entries:
        glosses = [g.text for e in r.entries[:1] for s in e.senses for g in s.glosses if g.lang == "eng"][:3]
        print("JMDict OK:", glosses)
    else:
        print("JMDict: no result")
except Exception as ex:
    print("JMDict error:", ex)

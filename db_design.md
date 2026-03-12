# NHK Easy Japanese Reader - DB 설계 문서

## 1. 개요

이 문서는 NHK Easy 일본어 학습 앱의 PostgreSQL 기반 저장 구조 설계를 설명합니다.
PC와 휴대폰에서 동일한 데이터를 사용하고, 향후 멀티 사용자 계정별 데이터 분리를 지원하기 위한 스키마입니다.

---

## 2. 테이블 관계

```
users
  ├── user_words (1:N) ──► words (N:1)
  ├── word_occurrences (1:N) ──► words (N:1)
  │                         └── articles (N:1)
  │                         └── article_sentences (N:1, optional)
  └── review_logs (1:N) ──► words (N:1)

articles
  └── article_sentences (1:N)

words
  └── word_surface_variants (1:N)
```

---

## 3. 설계 원칙

### 3.1 words와 user_words를 분리한 이유

| 구분 | words | user_words |
|------|-------|-------------|
| 역할 | 단어 **자체** 정보 (lemma, reading, meanings, pos) | 사용자 **별** 학습 상태 |
| 공유 여부 | 모든 사용자가 공유 | 사용자마다 독립 |
| 예시 | 津波(つなみ, 쓰나미) | A 사용자: learning, B 사용자: known |

**분리 이유:**
1. **데이터 중복 제거**: 같은 단어를 여러 사용자가 저장해도 `words`에는 1건만 존재
2. **사전 정보 일원화**: lemma, reading, meanings는 사전/형태소 분석 결과로, 사용자와 무관
3. **멀티 사용자 확장**: 사용자 A의 "아직 모름"과 사용자 B의 "외움" 상태를 독립적으로 관리
4. **저장 공간 효율**: 단어 정보는 한 번만 저장하고, 사용자별 상태만 user_words에 저장

### 3.2 word_occurrences가 필요한 이유

`word_occurrences`는 **"이 사용자가 이 단어를 어느 기사/문장에서 봤는지"** 기록합니다.

**필요한 이유:**
1. **예문 표시**: 단어장/복습에서 "이 단어가 나온 예문"을 보여줄 때 사용
2. **관련 기사 연결**: 단어별로 어떤 기사에서 등장했는지 조회
3. **문맥 보존**: `context_sentence`, `context_translation`으로 저장 당시 문장/번역 유지
4. **다시 등장 추적**: 같은 단어가 여러 기사에서 반복 등장 시 seen_count 등 갱신에 활용

**user_words와의 차이:**
- `user_words`: "이 단어를 저장했고, 현재 상태는 learning/review/known"
- `word_occurrences`: "이 단어를 이 문장(기사)에서 봤다" — **등장 이력**

### 3.3 기사 / 문장 / 단어 / 사용자 관계

```
[articles] 1 ──► N [article_sentences]
    │                      │
    │                      │ (문장에서 추출된 단어)
    │                      ▼
    │               [words] ◄──── [word_surface_variants]
    │                  │
    │                  │ (사용자가 저장/학습)
    ▼                  ▼
[word_occurrences] ◄── [user_words]
    │                      │
    └── user_id ───────────┘
```

- **articles**: NHK 기사 원문, URL 기준 유니크
- **article_sentences**: 기사 본문을 문장 단위로 분리, order_no로 순서 유지
- **words**: lemma 기준 단어 마스터 (사전 정보)
- **word_surface_variants**: 같은 lemma의 다양한 표기 (起こる/起こりました 등)
- **user_words**: 사용자별 저장 여부, status(learning/review/known), 메모
- **word_occurrences**: 사용자가 특정 기사/문장에서 단어를 저장한 기록

### 3.4 향후 로그인 기능 확장

현재 `users` 테이블에 `password_hash`, `email`이 nullable로 준비되어 있습니다.

**확장 시나리오:**
1. **로그인 추가**: `password_hash` 저장, 세션/토큰으로 `user_id` 식별
2. **기존 데이터 유지**: `default_user`로 저장된 데이터는 그대로 유지
3. **계정 이전**: 필요 시 `default_user`의 user_words/word_occurrences를 새 계정으로 이전하는 마이그레이션 스크립트 작성
4. **OAuth 연동**: `password_hash` 대신 외부 provider id 저장용 컬럼 추가 가능

---

## 4. 앱 기능 ↔ DB 스키마 매핑

### 4.1 기사 Fetch (fetch_article_body, cache_article)

| 앱 동작 | DB 작업 |
|---------|---------|
| RSS에서 기사 목록 가져오기 | (메모리/캐시만, DB 미사용) |
| 기사 본문 fetch | `articles` UPSERT (url 기준) |
| 기사 본문 캐시 조회 | `articles` SELECT WHERE url = ? |

**테이블:** `articles`

---

### 4.2 문장별 읽기 (split_sentences → 문장 카드)

| 앱 동작 | DB 작업 |
|---------|---------|
| 기사 본문 문장 분리 | `article_sentences` INSERT (article_id, order_no, sentence_text, sentence_translation) |
| 문장별 단어 칩 표시 | 형태소 분석 → `words` 조회/생성, `word_surface_variants` 조회/생성 |

**테이블:** `articles`, `article_sentences`, `words`, `word_surface_variants`

---

### 4.3 단어 저장 (remember_word, 팝업에서 저장하기)

| 앱 동작 | DB 작업 |
|---------|---------|
| 단어 저장 클릭 | 1. `words` UPSERT (lemma, reading, meanings, pos) |
| | 2. `word_surface_variants` UPSERT (surface) |
| | 3. `user_words` UPSERT (user_id, word_id, saved=true, status=learning) |
| | 4. `word_occurrences` INSERT (user_id, word_id, article_id, sentence_id, context_sentence, context_translation) |

**테이블:** `words`, `word_surface_variants`, `user_words`, `word_occurrences`

---

### 4.4 단어장 조회 (load_words, 필터/정렬)

| 앱 동작 | DB 작업 |
|---------|---------|
| 저장된 단어 목록 | `user_words` JOIN `words` WHERE user_id=? AND saved=true |
| 상태 필터 (학습중/복습/암기완료) | WHERE status IN (?) |
| 정렬 (최근 저장순/많이 본 순/lemma순) | ORDER BY last_seen_at DESC / seen_count DESC / lemma |
| 검색 (lemma, 읽기, 뜻) | words.lemma, words.reading, words.meanings @> 검색 |

**테이블:** `user_words`, `words`

---

### 4.5 단어장 상세 (관련 기사, 예문)

| 앱 동작 | DB 작업 |
|---------|---------|
| 관련 기사 목록 | `word_occurrences` JOIN `articles` WHERE user_id=? AND word_id=? GROUP BY article_id |
| 예문 목록 | `word_occurrences` WHERE user_id=? AND word_id=? ORDER BY seen_at DESC |

**테이블:** `word_occurrences`, `articles`

---

### 4.6 복습 페이지 (to_review, 자가평가)

| 앱 동작 | DB 작업 |
|---------|---------|
| 복습할 단어 목록 | `user_words` JOIN `words` WHERE user_id=? AND saved=true AND status IN ('learning','review') |
| 정렬 (최근 저장순/랜덤) | ORDER BY last_seen_at / RANDOM() |
| 자가평가 (아직 모름/애매함/외움) | 1. `user_words` UPDATE status, last_seen_at |
| | 2. `review_logs` INSERT (user_id, word_id, result) |

**테이블:** `user_words`, `words`, `review_logs`

---

### 4.7 복습 예문 표시 (get_word_occurrences)

| 앱 동작 | DB 작업 |
|---------|---------|
| 단어별 예문 1~2개 | `word_occurrences` WHERE user_id=? AND word_id=? ORDER BY seen_at DESC LIMIT 2 |

**테이블:** `word_occurrences`

---

### 4.8 대시보드 통계

| 앱 동작 | DB 작업 |
|---------|---------|
| 저장 단어 수 | `user_words` COUNT WHERE user_id=? AND saved=true |
| 오늘 복습 단어 수 | `user_words` COUNT WHERE user_id=? AND status IN ('learning','review') |
| 읽은 기사 수 | `articles` COUNT (또는 user별 읽은 기사 테이블 추가 시) |

**테이블:** `user_words`, `articles`

---

## 5. 매핑 요약표

| 앱 기능 | 주 테이블 | 보조 테이블 |
|---------|-----------|-------------|
| 기사 fetch/캐시 | articles | - |
| 문장 저장 | article_sentences | articles |
| 단어 저장 | words, user_words, word_occurrences | word_surface_variants, articles |
| 단어장 조회 | user_words, words | - |
| 관련 기사/예문 | word_occurrences | articles |
| 복습 목록 | user_words, words | - |
| 복습 평가 | user_words, review_logs | - |

---

## 6. 파일 구성

| 파일 | 설명 |
|------|------|
| `schema.sql` | DDL (테이블, 인덱스, 제약, 트리거) |
| `sample_seed.sql` | 초기 사용자(default_user) seed |
| `db_design.md` | 본 설계 문서 |

---

## 7. 적용 방법

```bash
# 1. PostgreSQL DB 생성
createdb nhk_easy_reader

# 2. 스키마 적용
psql -d nhk_easy_reader -f schema.sql

# 3. Seed 데이터 적용
psql -d nhk_easy_reader -f sample_seed.sql
```

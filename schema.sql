-- =============================================================================
-- NHK Easy Japanese Reader - PostgreSQL Schema
-- 멀티 사용자 확장을 고려한 스키마 설계
-- =============================================================================

-- Drop 순서 (의존성 역순)
DROP TABLE IF EXISTS review_logs CASCADE;
DROP TABLE IF EXISTS word_occurrences CASCADE;
DROP TABLE IF EXISTS user_words CASCADE;
DROP TABLE IF EXISTS word_surface_variants CASCADE;
DROP TABLE IF EXISTS article_sentences CASCADE;
DROP TABLE IF EXISTS words CASCADE;
DROP TABLE IF EXISTS articles CASCADE;
DROP TABLE IF EXISTS users CASCADE;

DROP FUNCTION IF EXISTS set_updated_at() CASCADE;

-- =============================================================================
-- Trigger: updated_at 자동 갱신
-- =============================================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 1. users
-- =============================================================================
CREATE TABLE users (
  id              bigserial PRIMARY KEY,
  username        varchar(100) NOT NULL UNIQUE,
  email           varchar(255) UNIQUE,
  password_hash   varchar(255),
  display_name    varchar(100),
  is_active       boolean NOT NULL DEFAULT true,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_is_active ON users(is_active) WHERE is_active = true;

-- =============================================================================
-- 2. articles
-- =============================================================================
CREATE TABLE articles (
  id                bigserial PRIMARY KEY,
  source            varchar(50) NOT NULL DEFAULT 'nhk_easy',
  source_article_key varchar(255),
  url               text NOT NULL UNIQUE,
  title             text NOT NULL,
  published_at      timestamptz,
  body_text         text NOT NULL,
  body_translation  text,
  raw_payload       jsonb,
  fetched_at        timestamptz NOT NULL DEFAULT now(),
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_articles_url ON articles(url);
CREATE INDEX idx_articles_source ON articles(source);
CREATE INDEX idx_articles_fetched_at ON articles(fetched_at DESC);

CREATE TRIGGER tr_articles_updated_at
  BEFORE UPDATE ON articles
  FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

-- =============================================================================
-- 3. article_sentences
-- =============================================================================
CREATE TABLE article_sentences (
  id                  bigserial PRIMARY KEY,
  article_id          bigint NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  order_no            integer NOT NULL,
  sentence_text       text NOT NULL,
  sentence_translation text,
  sentence_reading   text,
  created_at          timestamptz NOT NULL DEFAULT now(),
  UNIQUE(article_id, order_no)
);

CREATE INDEX idx_article_sentences_article_id ON article_sentences(article_id);
CREATE INDEX idx_article_sentences_article_order ON article_sentences(article_id, order_no);

-- =============================================================================
-- 4. words (단어 마스터 - 사용자 상태 없음)
-- =============================================================================
CREATE TABLE words (
  id                bigserial PRIMARY KEY,
  lemma             text NOT NULL,
  normalized_lemma  text NOT NULL,
  reading           text,
  pos               varchar(100),
  meanings          jsonb,
  dictionary_source varchar(50),
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now(),
  UNIQUE(normalized_lemma)
);

CREATE INDEX idx_words_lemma ON words(lemma);
CREATE INDEX idx_words_normalized_lemma ON words(normalized_lemma);
CREATE INDEX idx_words_meanings_gin ON words USING gin(meanings) WHERE meanings IS NOT NULL;

CREATE TRIGGER tr_words_updated_at
  BEFORE UPDATE ON words
  FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

-- =============================================================================
-- 5. word_surface_variants
-- =============================================================================
CREATE TABLE word_surface_variants (
  id        bigserial PRIMARY KEY,
  word_id   bigint NOT NULL REFERENCES words(id) ON DELETE CASCADE,
  surface   text NOT NULL,
  reading   text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(word_id, surface)
);

CREATE INDEX idx_word_surface_variants_word_id ON word_surface_variants(word_id);

-- =============================================================================
-- 6. user_words (사용자별 단어 저장/학습 상태)
-- =============================================================================
CREATE TABLE user_words (
  id             bigserial PRIMARY KEY,
  user_id        bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  word_id        bigint NOT NULL REFERENCES words(id) ON DELETE CASCADE,
  saved          boolean NOT NULL DEFAULT true,
  status         varchar(20) NOT NULL DEFAULT 'learning',
  memo           text,
  difficulty     smallint,
  first_seen_at  timestamptz,
  last_seen_at   timestamptz,
  saved_at       timestamptz NOT NULL DEFAULT now(),
  seen_count     integer NOT NULL DEFAULT 0,
  review_count   integer NOT NULL DEFAULT 0,
  correct_count  integer NOT NULL DEFAULT 0,
  incorrect_count integer NOT NULL DEFAULT 0,
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now(),
  UNIQUE(user_id, word_id),
  CHECK (status IN ('learning', 'review', 'known'))
);

CREATE INDEX idx_user_words_user_id ON user_words(user_id);
CREATE INDEX idx_user_words_word_id ON user_words(word_id);
CREATE INDEX idx_user_words_user_status ON user_words(user_id, status) WHERE saved = true;
CREATE INDEX idx_user_words_last_seen ON user_words(user_id, last_seen_at DESC NULLS LAST) WHERE saved = true;

CREATE TRIGGER tr_user_words_updated_at
  BEFORE UPDATE ON user_words
  FOR EACH ROW EXECUTE PROCEDURE set_updated_at();

-- =============================================================================
-- 7. word_occurrences (사용자별 단어 등장 기록)
-- =============================================================================
CREATE TABLE word_occurrences (
  id                 bigserial PRIMARY KEY,
  user_id            bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  word_id            bigint NOT NULL REFERENCES words(id) ON DELETE CASCADE,
  article_id         bigint NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
  sentence_id        bigint REFERENCES article_sentences(id) ON DELETE SET NULL,
  surface            text NOT NULL,
  occurrence_order   integer,
  context_sentence   text NOT NULL,
  context_translation text,
  seen_at            timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_word_occurrences_user_word ON word_occurrences(user_id, word_id);
CREATE INDEX idx_word_occurrences_article_id ON word_occurrences(article_id);
CREATE INDEX idx_word_occurrences_sentence_id ON word_occurrences(sentence_id);
CREATE INDEX idx_word_occurrences_seen_at ON word_occurrences(user_id, word_id, seen_at DESC);

-- 중복 occurrence 방지: (user_id, word_id, article_id, sentence_id) unique (sentence_id NOT NULL인 경우)
CREATE UNIQUE INDEX idx_word_occurrences_unique_sentence
  ON word_occurrences (user_id, word_id, article_id, sentence_id)
  WHERE sentence_id IS NOT NULL;

-- =============================================================================
-- 8. review_logs (복습 이력)
-- =============================================================================
CREATE TABLE review_logs (
  id          bigserial PRIMARY KEY,
  user_id     bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  word_id     bigint NOT NULL REFERENCES words(id) ON DELETE CASCADE,
  result      varchar(20) NOT NULL,
  reviewed_at timestamptz NOT NULL DEFAULT now(),
  note        text,
  CHECK (result IN ('learning', 'review', 'known', 'again', 'hard', 'good', 'easy'))
);

CREATE INDEX idx_review_logs_user_id ON review_logs(user_id);
CREATE INDEX idx_review_logs_word_id ON review_logs(word_id);
CREATE INDEX idx_review_logs_reviewed_at ON review_logs(user_id, reviewed_at DESC);

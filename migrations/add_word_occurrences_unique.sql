-- 중복 occurrence 방지: (user_id, word_id, article_id, sentence_id) unique
-- sentence_id가 NOT NULL인 경우에만 적용 (NULL은 application-level 체크)
-- 기존 DB에 적용 시: 중복이 있으면 실패할 수 있음. 먼저 중복 제거 필요.
CREATE UNIQUE INDEX IF NOT EXISTS idx_word_occurrences_unique_sentence
  ON word_occurrences (user_id, word_id, article_id, sentence_id)
  WHERE sentence_id IS NOT NULL;

-- =============================================================================
-- NHK Easy Japanese Reader - Seed Data
-- 초기 사용자 (default_user, master 테스트 계정)
-- =============================================================================
-- 실행 전 schema.sql 적용 필요
-- =============================================================================

-- 기본 사용자 1건 (레거시 호환)
INSERT INTO users (username, display_name, is_active)
VALUES ('default_user', '기본 사용자', true)
ON CONFLICT (username) DO NOTHING;

-- 테스트 계정: master / hulkhulk67!
INSERT INTO users (username, password_hash, display_name, is_active)
VALUES (
  'master',
  '3259609b50bcf90afeaa136df3ca74ab36b869193a069b90b2eeed1a487bba28',
  '테스트 관리자',
  true
)
ON CONFLICT (username) DO NOTHING;

-- 자동로그인 계정: leehuunjoo67@gmail.com / hulkhulk67!
INSERT INTO users (username, password_hash, display_name, is_active)
VALUES (
  'leehuunjoo67@gmail.com',
  '3259609b50bcf90afeaa136df3ca74ab36b869193a069b90b2eeed1a487bba28',
  '자동로그인',
  true
)
ON CONFLICT (username) DO NOTHING;

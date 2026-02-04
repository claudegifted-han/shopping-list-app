-- 외출/특별실 신청 스키마 업데이트

-- 1. share_type enum 생성
DO $$ BEGIN
  CREATE TYPE share_type AS ENUM ('private', 'link', 'public');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

-- 2. outing_type enum에 새 값 추가
ALTER TYPE outing_type ADD VALUE IF NOT EXISTS 'general_outing';
ALTER TYPE outing_type ADD VALUE IF NOT EXISTS 'general_overnight';
ALTER TYPE outing_type ADD VALUE IF NOT EXISTS 'research_outing';
ALTER TYPE outing_type ADD VALUE IF NOT EXISTS 'research_overnight';

-- 3. 새 컬럼 추가
ALTER TABLE outing_applications
  ADD COLUMN IF NOT EXISTS location VARCHAR(200),
  ADD COLUMN IF NOT EXISTS location_category VARCHAR(50),
  ADD COLUMN IF NOT EXISTS reason TEXT,
  ADD COLUMN IF NOT EXISTS date DATE,
  ADD COLUMN IF NOT EXISTS share_type share_type DEFAULT 'private';

-- 4. 기존 데이터 마이그레이션
UPDATE outing_applications SET
  location = COALESCE(title, ''),
  reason = description,
  date = DATE(start_time),
  share_type = CASE WHEN is_public THEN 'public'::share_type ELSE 'private'::share_type END
WHERE location IS NULL;

-- 5. old 'outing' 타입을 'general_outing'으로 변환
UPDATE outing_applications SET type = 'general_outing' WHERE type = 'outing';

-- 6. 필수 컬럼 기본값 설정
UPDATE outing_applications SET location = '' WHERE location IS NULL;
UPDATE outing_applications SET date = CURRENT_DATE WHERE date IS NULL;

-- 7. NOT NULL 제약조건 추가
ALTER TABLE outing_applications ALTER COLUMN location SET NOT NULL;
ALTER TABLE outing_applications ALTER COLUMN date SET NOT NULL;
ALTER TABLE outing_applications ALTER COLUMN share_type SET NOT NULL;

-- 8. RLS 정책 업데이트
DROP POLICY IF EXISTS "Users can view own outing applications" ON outing_applications;
CREATE POLICY "Users can view own outing applications" ON outing_applications
FOR SELECT
USING (
  auth.uid() = user_id
  OR share_type = 'public'
  OR share_type = 'link'
  OR EXISTS (
    SELECT 1 FROM profiles
    WHERE profiles.id = auth.uid()
    AND profiles.role IN ('teacher', 'admin')
  )
);

-- 9. 이전 컬럼 삭제
ALTER TABLE outing_applications DROP COLUMN IF EXISTS title;
ALTER TABLE outing_applications DROP COLUMN IF EXISTS description;
ALTER TABLE outing_applications DROP COLUMN IF EXISTS is_public;

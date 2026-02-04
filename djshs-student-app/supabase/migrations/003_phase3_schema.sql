-- Phase 3: 벌점, 알림 스키마

-- ENUM 타입 생성
CREATE TYPE notification_type AS ENUM ('penalty', 'study', 'outing', 'system');

-- 벌점 사유 테이블
CREATE TABLE penalty_reasons (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(200) NOT NULL,
  points INT NOT NULL,
  category VARCHAR(100),
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 벌점 기록 테이블
CREATE TABLE penalty_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reason_id UUID REFERENCES penalty_reasons(id) ON DELETE SET NULL,
  issued_by UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  points INT NOT NULL,
  description TEXT,
  issued_date DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 벌점 대상 테이블 (다대다 관계)
CREATE TABLE penalty_record_targets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  record_id UUID NOT NULL REFERENCES penalty_records(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(record_id, user_id)
);

-- 알림 테이블
CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  title VARCHAR(200) NOT NULL,
  message TEXT,
  type notification_type NOT NULL,
  is_read BOOLEAN DEFAULT false,
  related_id UUID,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  read_at TIMESTAMPTZ
);

-- 인덱스 생성
CREATE INDEX idx_penalty_reasons_active ON penalty_reasons(is_active);
CREATE INDEX idx_penalty_records_issued_by ON penalty_records(issued_by);
CREATE INDEX idx_penalty_records_issued_date ON penalty_records(issued_date);
CREATE INDEX idx_penalty_record_targets_record_id ON penalty_record_targets(record_id);
CREATE INDEX idx_penalty_record_targets_user_id ON penalty_record_targets(user_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

-- RLS 활성화
ALTER TABLE penalty_reasons ENABLE ROW LEVEL SECURITY;
ALTER TABLE penalty_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE penalty_record_targets ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- penalty_reasons RLS 정책
CREATE POLICY "Anyone can view active penalty reasons"
  ON penalty_reasons FOR SELECT
  USING (is_active = true OR EXISTS (
    SELECT 1 FROM profiles
    WHERE profiles.id = auth.uid()
    AND profiles.role IN ('teacher', 'admin')
  ));

CREATE POLICY "Teachers can manage penalty reasons"
  ON penalty_reasons FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('teacher', 'admin')
    )
  );

-- penalty_records RLS 정책
CREATE POLICY "Users can view penalty records they're involved in"
  ON penalty_records FOR SELECT
  USING (
    issued_by = auth.uid()
    OR EXISTS (
      SELECT 1 FROM penalty_record_targets
      WHERE penalty_record_targets.record_id = penalty_records.id
      AND penalty_record_targets.user_id = auth.uid()
    )
    OR EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('teacher', 'admin')
    )
  );

CREATE POLICY "Teachers can create penalty records"
  ON penalty_records FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('teacher', 'admin')
    )
  );

CREATE POLICY "Teachers can update penalty records"
  ON penalty_records FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('teacher', 'admin')
    )
  );

-- penalty_record_targets RLS 정책
CREATE POLICY "Users can view their penalty targets"
  ON penalty_record_targets FOR SELECT
  USING (
    user_id = auth.uid()
    OR EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('teacher', 'admin')
    )
  );

CREATE POLICY "Teachers can manage penalty targets"
  ON penalty_record_targets FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('teacher', 'admin')
    )
  );

-- notifications RLS 정책
CREATE POLICY "Users can view own notifications"
  ON notifications FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "Users can update own notifications"
  ON notifications FOR UPDATE
  USING (user_id = auth.uid());

CREATE POLICY "System can create notifications"
  ON notifications FOR INSERT
  WITH CHECK (true);

-- updated_at 트리거 적용
CREATE TRIGGER update_penalty_reasons_updated_at
  BEFORE UPDATE ON penalty_reasons
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_penalty_records_updated_at
  BEFORE UPDATE ON penalty_records
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- 프로필에 총 벌점 컬럼 추가
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS total_penalty INT DEFAULT 0;

-- 벌점 합계 업데이트 함수
CREATE OR REPLACE FUNCTION update_user_total_penalty()
RETURNS TRIGGER AS $$
DECLARE
  target_user_id UUID;
  new_total INT;
BEGIN
  IF TG_OP = 'INSERT' THEN
    target_user_id := NEW.user_id;
  ELSIF TG_OP = 'DELETE' THEN
    target_user_id := OLD.user_id;
  END IF;

  SELECT COALESCE(SUM(pr.points), 0) INTO new_total
  FROM penalty_record_targets prt
  JOIN penalty_records pr ON pr.id = prt.record_id
  WHERE prt.user_id = target_user_id;

  UPDATE profiles SET total_penalty = new_total WHERE id = target_user_id;

  IF TG_OP = 'INSERT' THEN
    RETURN NEW;
  ELSE
    RETURN OLD;
  END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_total_penalty_on_target_change
  AFTER INSERT OR DELETE ON penalty_record_targets
  FOR EACH ROW
  EXECUTE FUNCTION update_user_total_penalty();

-- 샘플 벌점 사유 데이터
INSERT INTO penalty_reasons (title, points, category, is_active) VALUES
  -- 상점 (음수가 아닌 양수로 표현, 실제로는 벌점 감소)
  ('매월 퇴실 지각자가 한 명도 없는 학급', -2, '상점', true),
  ('봉사활동 참여', -1, '상점', true),
  ('모범학생 표창', -3, '상점', true),
  ('자습실 정리정돈 우수', -1, '상점', true),

  -- 벌점
  ('지각 (5분 이내)', 1, '출결', true),
  ('지각 (5분 초과)', 2, '출결', true),
  ('무단결석', 5, '출결', true),
  ('무단 조퇴', 3, '출결', true),
  ('야간자습 무단이탈', 3, '자습', true),
  ('자습시간 소란', 2, '자습', true),
  ('휴대폰 사용 적발', 3, '생활', true),
  ('외출증 미지참', 2, '생활', true),
  ('기숙사 규칙 위반', 3, '기숙사', true),
  ('청소 불이행', 1, '기숙사', true),
  ('소등시간 미준수', 2, '기숙사', true);

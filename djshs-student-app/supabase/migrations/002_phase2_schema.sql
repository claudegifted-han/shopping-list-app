-- Phase 2: 자습, 외출/특별실, 기숙사 스키마

-- ENUM 타입 생성
CREATE TYPE application_status AS ENUM ('pending', 'approved', 'rejected', 'cancelled', 'completed');
CREATE TYPE outing_type AS ENUM ('outing', 'special_room');
CREATE TYPE dormitory_type AS ENUM ('today', 'tomorrow');

-- 독서실 좌석 테이블
CREATE TABLE study_seats (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  room_name VARCHAR(100) NOT NULL,
  seat_number VARCHAR(20) NOT NULL,
  is_available BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(room_name, seat_number)
);

-- 자습 신청 테이블
CREATE TABLE study_applications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  seat_id UUID NOT NULL REFERENCES study_seats(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  status application_status DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, date),
  UNIQUE(seat_id, date)
);

-- 외출/특별실 신청 테이블
CREATE TABLE outing_applications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  title VARCHAR(200) NOT NULL,
  description TEXT,
  type outing_type NOT NULL,
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ NOT NULL,
  status application_status DEFAULT 'pending',
  is_public BOOLEAN DEFAULT false,
  approved_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 기숙사 신청 테이블
CREATE TABLE dormitory_applications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  type dormitory_type NOT NULL,
  status application_status DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, date, type)
);

-- 인덱스 생성
CREATE INDEX idx_study_applications_user_id ON study_applications(user_id);
CREATE INDEX idx_study_applications_date ON study_applications(date);
CREATE INDEX idx_study_applications_seat_id ON study_applications(seat_id);
CREATE INDEX idx_outing_applications_user_id ON outing_applications(user_id);
CREATE INDEX idx_outing_applications_status ON outing_applications(status);
CREATE INDEX idx_dormitory_applications_user_id ON dormitory_applications(user_id);
CREATE INDEX idx_dormitory_applications_date ON dormitory_applications(date);

-- RLS 활성화
ALTER TABLE study_seats ENABLE ROW LEVEL SECURITY;
ALTER TABLE study_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE outing_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE dormitory_applications ENABLE ROW LEVEL SECURITY;

-- study_seats RLS 정책
CREATE POLICY "Anyone can view study seats"
  ON study_seats FOR SELECT
  USING (true);

CREATE POLICY "Teachers can manage study seats"
  ON study_seats FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('teacher', 'admin')
    )
  );

-- study_applications RLS 정책
CREATE POLICY "Users can view all study applications"
  ON study_applications FOR SELECT
  USING (true);

CREATE POLICY "Users can create own study applications"
  ON study_applications FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own study applications"
  ON study_applications FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Teachers can manage all study applications"
  ON study_applications FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('teacher', 'admin')
    )
  );

-- outing_applications RLS 정책
CREATE POLICY "Users can view own outing applications"
  ON outing_applications FOR SELECT
  USING (
    auth.uid() = user_id
    OR is_public = true
    OR EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('teacher', 'admin')
    )
  );

CREATE POLICY "Users can create own outing applications"
  ON outing_applications FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own outing applications"
  ON outing_applications FOR UPDATE
  USING (auth.uid() = user_id AND status = 'pending');

CREATE POLICY "Teachers can manage all outing applications"
  ON outing_applications FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('teacher', 'admin')
    )
  );

-- dormitory_applications RLS 정책
CREATE POLICY "Users can view own dormitory applications"
  ON dormitory_applications FOR SELECT
  USING (
    auth.uid() = user_id
    OR EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('teacher', 'admin')
    )
  );

CREATE POLICY "Users can create own dormitory applications"
  ON dormitory_applications FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own dormitory applications"
  ON dormitory_applications FOR UPDATE
  USING (auth.uid() = user_id AND status = 'pending');

CREATE POLICY "Teachers can manage all dormitory applications"
  ON dormitory_applications FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM profiles
      WHERE profiles.id = auth.uid()
      AND profiles.role IN ('teacher', 'admin')
    )
  );

-- updated_at 트리거 함수 (이미 존재할 수 있음)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- updated_at 트리거 적용
CREATE TRIGGER update_study_applications_updated_at
  BEFORE UPDATE ON study_applications
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_outing_applications_updated_at
  BEFORE UPDATE ON outing_applications
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dormitory_applications_updated_at
  BEFORE UPDATE ON dormitory_applications
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- 샘플 독서실 좌석 데이터
INSERT INTO study_seats (room_name, seat_number) VALUES
  ('독서실 A', 'A1'), ('독서실 A', 'A2'), ('독서실 A', 'A3'), ('독서실 A', 'A4'), ('독서실 A', 'A5'),
  ('독서실 A', 'A6'), ('독서실 A', 'A7'), ('독서실 A', 'A8'), ('독서실 A', 'A9'), ('독서실 A', 'A10'),
  ('독서실 B', 'B1'), ('독서실 B', 'B2'), ('독서실 B', 'B3'), ('독서실 B', 'B4'), ('독서실 B', 'B5'),
  ('독서실 B', 'B6'), ('독서실 B', 'B7'), ('독서실 B', 'B8'), ('독서실 B', 'B9'), ('독서실 B', 'B10'),
  ('독서실 C', 'C1'), ('독서실 C', 'C2'), ('독서실 C', 'C3'), ('독서실 C', 'C4'), ('독서실 C', 'C5'),
  ('독서실 C', 'C6'), ('독서실 C', 'C7'), ('독서실 C', 'C8'), ('독서실 C', 'C9'), ('독서실 C', 'C10');

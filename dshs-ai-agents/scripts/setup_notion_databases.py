#!/usr/bin/env python3
"""
DSHS AI Agent System - Notion 데이터베이스 자동 생성 스크립트
대전과학고등학교 AI 에이전트 시스템을 위한 Notion 데이터베이스 자동 설정

Usage:
    python setup_notion_databases.py --api-key YOUR_API_KEY --parent-page PAGE_ID

    또는 환경변수 사용:
    export NOTION_API_KEY=your_api_key
    export NOTION_PARENT_PAGE=your_parent_page_id
    python setup_notion_databases.py
"""

import os
import json
import argparse
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    import requests
except ImportError:
    print("requests 라이브러리가 필요합니다. pip install requests 로 설치하세요.")
    exit(1)


NOTION_API_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"


@dataclass
class DatabaseSchema:
    """데이터베이스 스키마 정의"""
    name: str
    icon: str
    description: str
    properties: Dict[str, Any]
    security_level: str


# 데이터베이스 스키마 정의
DATABASE_SCHEMAS: Dict[str, DatabaseSchema] = {
    "students": DatabaseSchema(
        name="학생 명부",
        icon="👨‍🎓",
        description="대전과학고 학생 명부 (보안등급: High)",
        security_level="high",
        properties={
            "이름": {"title": {}},
            "학번": {"rich_text": {}},
            "학년": {
                "select": {
                    "options": [
                        {"name": "1학년", "color": "blue"},
                        {"name": "2학년", "color": "green"},
                        {"name": "3학년", "color": "red"}
                    ]
                }
            },
            "반": {
                "select": {
                    "options": [
                        {"name": "1반", "color": "blue"},
                        {"name": "2반", "color": "green"},
                        {"name": "3반", "color": "yellow"}
                    ]
                }
            },
            "번호": {"number": {"format": "number"}},
            "상태": {
                "select": {
                    "options": [
                        {"name": "재학", "color": "green"},
                        {"name": "휴학", "color": "yellow"},
                        {"name": "졸업", "color": "gray"}
                    ]
                }
            }
        }
    ),

    "teachers": DatabaseSchema(
        name="교직원 명부",
        icon="👨‍🏫",
        description="대전과학고 교직원 명부 (보안등급: High)",
        security_level="high",
        properties={
            "이름": {"title": {}},
            "직위": {
                "select": {
                    "options": [
                        {"name": "교장", "color": "red"},
                        {"name": "교감", "color": "orange"},
                        {"name": "부장", "color": "yellow"},
                        {"name": "교사", "color": "green"},
                        {"name": "직원", "color": "blue"}
                    ]
                }
            },
            "부서": {
                "select": {
                    "options": [
                        {"name": "교무운영부", "color": "red"},
                        {"name": "교육과정부", "color": "orange"},
                        {"name": "교육평가부", "color": "yellow"},
                        {"name": "교육연구부", "color": "green"},
                        {"name": "교육정보부", "color": "blue"},
                        {"name": "학생생활안전부", "color": "purple"},
                        {"name": "방과후인성부", "color": "pink"},
                        {"name": "진로진학부", "color": "brown"},
                        {"name": "사감부", "color": "gray"},
                        {"name": "1학년부", "color": "blue"},
                        {"name": "2학년부", "color": "green"},
                        {"name": "3학년부", "color": "red"},
                        {"name": "과학교육부", "color": "yellow"},
                        {"name": "영재교육부", "color": "orange"},
                        {"name": "국제교류부", "color": "purple"},
                        {"name": "입학지원부", "color": "pink"}
                    ]
                }
            },
            "담당과목": {
                "multi_select": {
                    "options": [
                        {"name": "수학", "color": "blue"},
                        {"name": "물리", "color": "red"},
                        {"name": "화학", "color": "green"},
                        {"name": "생물", "color": "yellow"},
                        {"name": "지구과학", "color": "brown"},
                        {"name": "정보과학", "color": "purple"},
                        {"name": "국어", "color": "gray"},
                        {"name": "영어", "color": "pink"},
                        {"name": "사회", "color": "orange"}
                    ]
                }
            },
            "이메일": {"email": {}},
            "내선번호": {"rich_text": {}}
        }
    ),

    "research": DatabaseSchema(
        name="자율연구 현황",
        icon="🔬",
        description="대전과학고 자율연구 프로젝트 현황",
        security_level="standard",
        properties={
            "연구제목": {"title": {}},
            "연구유형": {
                "select": {
                    "options": [
                        {"name": "기초연구", "color": "blue"},
                        {"name": "심화연구", "color": "green"},
                        {"name": "졸업논문", "color": "red"}
                    ]
                }
            },
            "학년": {
                "select": {
                    "options": [
                        {"name": "1학년", "color": "blue"},
                        {"name": "2학년", "color": "green"},
                        {"name": "3학년", "color": "red"}
                    ]
                }
            },
            "분야": {
                "select": {
                    "options": [
                        {"name": "수학", "color": "blue"},
                        {"name": "물리", "color": "red"},
                        {"name": "화학", "color": "green"},
                        {"name": "생물", "color": "yellow"},
                        {"name": "지구과학", "color": "brown"},
                        {"name": "정보과학", "color": "purple"},
                        {"name": "융합", "color": "pink"}
                    ]
                }
            },
            "상태": {
                "select": {
                    "options": [
                        {"name": "계획중", "color": "gray"},
                        {"name": "진행중", "color": "blue"},
                        {"name": "완료", "color": "green"},
                        {"name": "보류", "color": "yellow"}
                    ]
                }
            },
            "시작일": {"date": {}},
            "종료일": {"date": {}},
            "예산": {"number": {"format": "number"}}
        }
    ),

    "events": DatabaseSchema(
        name="학사일정",
        icon="📅",
        description="대전과학고 학사일정",
        security_level="standard",
        properties={
            "일정명": {"title": {}},
            "유형": {
                "select": {
                    "options": [
                        {"name": "시험", "color": "red"},
                        {"name": "행사", "color": "blue"},
                        {"name": "연구", "color": "green"},
                        {"name": "방학", "color": "yellow"},
                        {"name": "회의", "color": "purple"},
                        {"name": "입학", "color": "pink"},
                        {"name": "졸업", "color": "orange"}
                    ]
                }
            },
            "시작일": {"date": {}},
            "종료일": {"date": {}},
            "담당부서": {
                "multi_select": {
                    "options": [
                        {"name": "교무운영부", "color": "red"},
                        {"name": "교육과정부", "color": "orange"},
                        {"name": "교육평가부", "color": "yellow"},
                        {"name": "영재교육부", "color": "green"},
                        {"name": "입학지원부", "color": "blue"}
                    ]
                }
            },
            "대상": {
                "multi_select": {
                    "options": [
                        {"name": "1학년", "color": "blue"},
                        {"name": "2학년", "color": "green"},
                        {"name": "3학년", "color": "red"},
                        {"name": "전교생", "color": "purple"},
                        {"name": "교직원", "color": "gray"}
                    ]
                }
            },
            "장소": {"rich_text": {}},
            "설명": {"rich_text": {}}
        }
    ),

    "meetings": DatabaseSchema(
        name="회의록",
        icon="📝",
        description="대전과학고 회의록",
        security_level="standard",
        properties={
            "회의명": {"title": {}},
            "일시": {"date": {}},
            "장소": {"rich_text": {}},
            "부서": {
                "select": {
                    "options": [
                        {"name": "전체", "color": "purple"},
                        {"name": "교무운영부", "color": "red"},
                        {"name": "교육과정부", "color": "orange"},
                        {"name": "교육평가부", "color": "yellow"},
                        {"name": "영재교육부", "color": "green"},
                        {"name": "기타", "color": "gray"}
                    ]
                }
            },
            "안건": {"rich_text": {}},
            "결정사항": {"rich_text": {}},
            "후속조치": {"rich_text": {}}
        }
    ),

    "documents": DatabaseSchema(
        name="공문/문서",
        icon="📄",
        description="대전과학고 공문 및 문서 관리",
        security_level="standard",
        properties={
            "제목": {"title": {}},
            "문서번호": {"rich_text": {}},
            "유형": {
                "select": {
                    "options": [
                        {"name": "공문", "color": "red"},
                        {"name": "가정통신문", "color": "blue"},
                        {"name": "보고서", "color": "green"},
                        {"name": "계획서", "color": "yellow"},
                        {"name": "안내문", "color": "purple"}
                    ]
                }
            },
            "작성부서": {
                "select": {
                    "options": [
                        {"name": "교무운영부", "color": "red"},
                        {"name": "교육과정부", "color": "orange"},
                        {"name": "교육평가부", "color": "yellow"},
                        {"name": "학생생활안전부", "color": "green"},
                        {"name": "기타", "color": "gray"}
                    ]
                }
            },
            "작성일": {"date": {}},
            "상태": {
                "select": {
                    "options": [
                        {"name": "초안", "color": "gray"},
                        {"name": "검토중", "color": "yellow"},
                        {"name": "완료", "color": "green"},
                        {"name": "발송완료", "color": "blue"}
                    ]
                }
            },
            "내용": {"rich_text": {}}
        }
    ),

    "clubs": DatabaseSchema(
        name="동아리",
        icon="🎭",
        description="대전과학고 동아리 현황",
        security_level="standard",
        properties={
            "동아리명": {"title": {}},
            "분류": {
                "select": {
                    "options": [
                        {"name": "학술", "color": "blue"},
                        {"name": "체육", "color": "green"},
                        {"name": "예술", "color": "red"},
                        {"name": "봉사", "color": "yellow"},
                        {"name": "기타", "color": "gray"}
                    ]
                }
            },
            "인원": {"number": {"format": "number"}},
            "활동요일": {
                "multi_select": {
                    "options": [
                        {"name": "월", "color": "red"},
                        {"name": "화", "color": "orange"},
                        {"name": "수", "color": "yellow"},
                        {"name": "목", "color": "green"},
                        {"name": "금", "color": "blue"}
                    ]
                }
            },
            "활동장소": {"rich_text": {}},
            "상태": {
                "select": {
                    "options": [
                        {"name": "활동중", "color": "green"},
                        {"name": "휴면", "color": "yellow"},
                        {"name": "해체", "color": "gray"}
                    ]
                }
            }
        }
    )
}


class NotionDatabaseSetup:
    """Notion 데이터베이스 설정 클래스"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": NOTION_API_VERSION,
            "Content-Type": "application/json"
        }
        self.created_databases: Dict[str, str] = {}

    def test_connection(self) -> bool:
        """API 연결 테스트"""
        try:
            response = requests.get(
                f"{NOTION_BASE_URL}/users/me",
                headers=self.headers
            )
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Notion API 연결 성공!")
                print(f"   Bot: {user_data.get('name', 'Unknown')}")
                return True
            else:
                print(f"❌ Notion API 연결 실패: {response.status_code}")
                print(f"   {response.text}")
                return False
        except Exception as e:
            print(f"❌ 연결 오류: {e}")
            return False

    def create_database(
        self,
        parent_page_id: str,
        db_key: str,
        schema: DatabaseSchema
    ) -> Optional[str]:
        """데이터베이스 생성"""
        payload = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "icon": {"type": "emoji", "emoji": schema.icon},
            "title": [{"type": "text", "text": {"content": schema.name}}],
            "description": [{"type": "text", "text": {"content": schema.description}}],
            "properties": schema.properties
        }

        try:
            response = requests.post(
                f"{NOTION_BASE_URL}/databases",
                headers=self.headers,
                json=payload
            )

            if response.status_code == 200:
                db_data = response.json()
                db_id = db_data["id"]
                print(f"✅ {schema.icon} {schema.name} 생성 완료 (ID: {db_id})")
                return db_id
            else:
                print(f"❌ {schema.name} 생성 실패: {response.status_code}")
                print(f"   {response.text}")
                return None
        except Exception as e:
            print(f"❌ {schema.name} 생성 오류: {e}")
            return None

    def setup_all_databases(self, parent_page_id: str) -> Dict[str, str]:
        """모든 데이터베이스 생성"""
        print("\n" + "="*60)
        print("🚀 DSHS AI Agent System - Notion 데이터베이스 설정")
        print("="*60 + "\n")

        for db_key, schema in DATABASE_SCHEMAS.items():
            print(f"\n📦 {schema.name} 생성 중...")
            db_id = self.create_database(parent_page_id, db_key, schema)
            if db_id:
                self.created_databases[db_key] = db_id

        return self.created_databases

    def generate_env_file(self, output_path: str = ".env.notion") -> None:
        """환경변수 파일 생성"""
        env_content = f"""# DSHS AI Agent System - Notion 설정
# 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Notion API Key
NOTION_API_KEY={self.api_key}

# Database IDs
"""
        for db_key, db_id in self.created_databases.items():
            env_key = f"NOTION_DB_{db_key.upper()}"
            env_content += f"{env_key}={db_id}\n"

        with open(output_path, "w") as f:
            f.write(env_content)

        print(f"\n✅ 환경변수 파일 생성: {output_path}")

    def generate_config_json(self, output_path: str = "notion_config.json") -> None:
        """설정 JSON 파일 생성"""
        config = {
            "generated_at": datetime.now().isoformat(),
            "databases": {}
        }

        for db_key, db_id in self.created_databases.items():
            schema = DATABASE_SCHEMAS[db_key]
            config["databases"][db_key] = {
                "id": db_id,
                "name": schema.name,
                "security_level": schema.security_level
            }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print(f"✅ 설정 파일 생성: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="DSHS AI Agent System - Notion 데이터베이스 자동 설정"
    )
    parser.add_argument(
        "--api-key", "-k",
        help="Notion API Key (또는 NOTION_API_KEY 환경변수)",
        default=os.environ.get("NOTION_API_KEY")
    )
    parser.add_argument(
        "--parent-page", "-p",
        help="상위 페이지 ID (또는 NOTION_PARENT_PAGE 환경변수)",
        default=os.environ.get("NOTION_PARENT_PAGE")
    )
    parser.add_argument(
        "--test-only", "-t",
        action="store_true",
        help="연결 테스트만 수행"
    )
    parser.add_argument(
        "--output-dir", "-o",
        help="출력 디렉토리",
        default="."
    )

    args = parser.parse_args()

    if not args.api_key:
        print("❌ Notion API Key가 필요합니다.")
        print("   --api-key 옵션 또는 NOTION_API_KEY 환경변수를 설정하세요.")
        exit(1)

    setup = NotionDatabaseSetup(args.api_key)

    # 연결 테스트
    if not setup.test_connection():
        exit(1)

    if args.test_only:
        print("\n✅ 연결 테스트 완료!")
        exit(0)

    if not args.parent_page:
        print("❌ 상위 페이지 ID가 필요합니다.")
        print("   --parent-page 옵션 또는 NOTION_PARENT_PAGE 환경변수를 설정하세요.")
        exit(1)

    # 데이터베이스 생성
    created = setup.setup_all_databases(args.parent_page)

    if created:
        print("\n" + "="*60)
        print("📊 생성 결과")
        print("="*60)

        for db_key, db_id in created.items():
            print(f"  • {DATABASE_SCHEMAS[db_key].name}: {db_id}")

        # 설정 파일 생성
        output_dir = args.output_dir
        setup.generate_env_file(os.path.join(output_dir, ".env.notion"))
        setup.generate_config_json(os.path.join(output_dir, "notion_config.json"))

        print("\n" + "="*60)
        print("🎉 설정 완료!")
        print("="*60)
        print("\n다음 단계:")
        print("1. .env.notion 파일의 내용을 .env 파일에 복사")
        print("2. notion_config.json 을 config/ 디렉토리로 이동")
        print("3. MCP 서버 설정 확인")
    else:
        print("\n❌ 데이터베이스 생성 실패")
        exit(1)


if __name__ == "__main__":
    main()

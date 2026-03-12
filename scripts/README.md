# DB 설정 스크립트

## 1. 비밀번호 설정

`data/settings.json`에 PostgreSQL 비밀번호를 추가하세요:

```json
{
  "DB_HOST": "localhost",
  "DB_PORT": 5432,
  "DB_NAME": "nhk_easy_reader",
  "DB_USER": "postgres",
  "DB_PASSWORD": "여기에_비밀번호_입력"
}
```

또는 `.env` 파일에:
```
DB_USER=postgres
DB_PASSWORD=여기에_비밀번호_입력
```

## 2. DB 초기화 실행

**방법 A** – 비밀번호를 settings.json에 넣은 경우:
```powershell
python scripts/setup_db.py
```

**방법 B** – 비밀번호를 아직 안 넣은 경우 (실행 시 입력):
```powershell
.\scripts\run_setup.ps1
```

**방법 C** – 환경변수로 비밀번호 전달:
```powershell
$env:DB_PASSWORD="비밀번호"; python scripts/setup_db.py
```

## 3. master 테스트 계정 (기존 DB에 추가)

이미 DB를 사용 중이라면 master 계정만 추가:

```powershell
python scripts/add_master_user.py
```

- 아이디: `master`
- 비밀번호: `hulkhulk67!`

## 4. 앱 실행

```powershell
python -m streamlit run app.py
```

- 최초 실행 시 로그인 화면 표시
- 로그인 후 대시보드로 이동
- 회원가입으로 새 계정 생성 가능

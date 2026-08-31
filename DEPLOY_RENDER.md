# 무료 배포 순서

## 1. GitHub 저장소 만들기

1. GitHub에 로그인합니다.
2. 오른쪽 위 `+` → `New repository`를 선택합니다.
3. 저장소 이름을 `train-watch`로 입력합니다.
4. `Create repository`를 누릅니다.
5. `Add file` → `Upload files`를 선택합니다.
6. 이 폴더의 파일을 모두 업로드합니다.
7. `Commit changes`를 누릅니다.

## 2. Render 배포

1. Render에 GitHub 계정으로 로그인합니다.
2. `New` → `Web Service`를 선택합니다.
3. `train-watch` 저장소를 연결합니다.
4. Runtime은 `Docker`를 선택합니다.
5. Root Directory는 파일을 저장한 위치로 지정합니다.
6. Plan은 `Free`를 선택합니다.
7. `Create Web Service`를 누릅니다.

## 3. 환경변수 등록

Render 서비스 화면에서 `Environment` → `Add Environment Variable`을 선택하고 아래 항목을 등록합니다.

```text
KORAIL_SERVICE_KEY = 새로 발급받은 인증키
TELEGRAM_BOT_TOKEN = 텔레그램 봇 토큰
SMTP_HOST = 메일 서버 주소
SMTP_PORT = 465
SMTP_USER = 발신 이메일
SMTP_PASSWORD = 메일 앱 비밀번호
```

인증키와 비밀번호는 화면이나 저장소에 기록하지 않습니다.

## 4. 스마트폰에서 사용

배포가 끝나면 Render가 `https://...onrender.com` 주소를 제공합니다. 이 주소를 스마트폰 브라우저에서 열어 사용합니다.

감시 중에는 무료 서버 절전 방지를 위해 화면을 완전히 닫지 않는 것이 안전합니다. 무료 플랜은 15분간 요청이 없으면 절전될 수 있습니다.

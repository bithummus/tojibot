# 『토지』 40주 Discord 독서 알림 봇

기간: 2026-09-28 ~ 2027-07-04

## 기능
- 날짜로 현재 주차/Day 자동 계산
- 확정된 40주 권·편·장·페이지 범위 표시
- 주당 236~237쪽을 7일로 균등 배분(하루 약 33~34쪽)
- 매일 스포일러 없는 짧은 대화 질문
- 일정 밖 날짜에는 발송하지 않음

## 설치
1. Discord 서버 → 서버 설정 → 연동(Integrations) → Webhooks → New Webhook.
2. 원하는 채널을 고르고 Webhook URL을 복사.
3. 이 프로젝트를 GitHub 저장소에 업로드.
4. GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret.
5. 이름을 `DISCORD_WEBHOOK_URL`, 값은 복사한 Webhook URL로 저장.
6. Actions 탭에서 `Daily Toji Reading Message`를 수동 실행해 테스트.

Webhook URL은 비밀번호처럼 취급하고 저장소 파일에 직접 넣지 마세요.

## 발송 시간
`.github/workflows/daily.yml`은 매일 20:17, `Asia/Seoul`로 설정되어 있습니다.
예를 들어 오전 8:30으로 바꾸려면:
`cron: '30 8 * * *'`

## 테스트
Actions에서 Run workflow를 누르고 `test_date`에 `2026-09-28`을 넣으면 1주차 Day 1을 시험 발송합니다.

로컬 미리보기:
`TEST_DATE=2026-09-28 python bot.py --preview`

## 설계 메모
주간 경계는 최종 40주 진도표 그대로입니다. 일일 경계는 '매일 부담을 비슷하게'라는 기준을 우선해
주간 페이지 수를 7등분했습니다. 현재 대화 질문은 목차만으로 작품 내용을 지어내지 않도록
인물·관계·공간·사회상·선택을 관찰하는 스포일러 없는 질문으로 구성했습니다.

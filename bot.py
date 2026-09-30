import os
import json
import sys
import urllib.request

from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo


ROOT = os.path.dirname(os.path.abspath(__file__))
KST = ZoneInfo("Asia/Seoul")


MORNING_CHEERS = [
    "오늘도 한 장씩 차근차근 읽어봐. 아자아자! 📚",
    "오늘 분량은 오늘의 내가 해결한다! 천천히 시작해봐.",
    "조금씩 읽다 보면 어느새 20권 완독! 오늘도 파이팅!",
    "부담 갖지 말고 일단 책부터 펼쳐보자. 오늘도 잘 읽어봐!",
    "하루치만 읽으면 돼. 오늘의 『토지』도 힘차게 출발!",
    "한꺼번에 몰아 읽지 말고 오늘 몫만 착실하게! 파이팅!",
    "오늘도 『토지』 세계로 출발! 재미있게 읽고 저녁에 다시 만나.",
    "딱 오늘 분량만 생각하기! 조금씩 꾸준히 가보자.",
    "벌써 여기까지 왔어. 오늘도 흐름 끊기지 않게 이어가봐!",
    "책 한 번 펼치기가 제일 어려워. 펼쳤으면 이미 절반 성공!",
]


def load_schedule():
    path = os.path.join(ROOT, "data", "schedule.json")

    with open(path, encoding="utf-8") as f:
        return json.load(f)


def find_current_schedule_by_date(target_date):
    target = target_date.isoformat()

    for week in load_schedule():
        if week["start"] <= target <= week["end"]:

            start_date = datetime.fromisoformat(
                week["start"]
            ).date()

            day_index = (
                target_date - start_date
            ).days

            return week, day_index

    return None, None


def progress_bar(day_index):
    completed = day_index + 1

    return "█" * completed + "░" * (7 - completed)


def morning_message(week, day_index):
    weekday = [
        "월", "화", "수", "목", "금", "토", "일"
    ][day_index]

    today_pages = week["daily_pages"][day_index]

    cumulative = sum(
        week["daily_pages"][: day_index + 1]
    )

    cheer = MORNING_CHEERS[
        (week["week"] + day_index) % len(MORNING_CHEERS)
    ]

    return f"""☀️ **좋은 아침! 『토지』 {week['week']}주차 · Day {day_index + 1} ({weekday})**

📖 **이번 주 진도**
{week['volume']} · {week['scope']}

🎯 **오늘 목표**
약 **{today_pages}쪽**

오늘까지 읽으면 주간 누적 **{cumulative}/{week['pages']}쪽**이야.

{cheer}

_오늘 분량을 조금 앞뒤로 조정해 읽어도 괜찮아. 장이 얼마 남지 않았다면 장 끝까지 읽는 걸 추천해._
"""


def evening_message(week, day_index):
    weekday = [
        "월", "화", "수", "목", "금", "토", "일"
    ][day_index]

    today_pages = week["daily_pages"][day_index]

    cumulative = sum(
        week["daily_pages"][: day_index + 1]
    )

    topic = week["daily_topics"][day_index]

    return f"""🌙 **『토지』 {week['week']}주차 · Day {day_index + 1} ({weekday})**

📖 **오늘 목표**
약 **{today_pages}쪽**

📚 **오늘까지 목표 진도**
주간 누적 **{cumulative}/{week['pages']}쪽**

**진행도**
{progress_bar(day_index)} {day_index + 1}/7

💬 **오늘의 짧은 이야기**
{topic}

오늘 분량 읽은 친구들은 편하게 한마디씩 남겨줘.
아직 못 읽었다면 괜찮아. 오늘 밤 조금이라도 이어가보자! 📖
"""


def build_message(week, day_index, message_type):
    if message_type == "morning":
        return morning_message(
            week,
            day_index
        )

    if message_type == "evening":
        return evening_message(
            week,
            day_index
        )

    raise ValueError(
        f"알 수 없는 MESSAGE_TYPE: {message_type}"
    )

def get_target_datetime(message_type):
    now = datetime.now(KST)

    if message_type == "morning":
        scheduled_hour = 8
        scheduled_minute = 0
    else:
        scheduled_hour = 20
        scheduled_minute = 17

    scheduled_today = now.replace(
        hour=scheduled_hour,
        minute=scheduled_minute,
        second=0,
        microsecond=0
    )

    # 아직 오늘의 해당 스케줄 시간이 오기 전이라면
    # 실행 중인 job은 전날 스케줄이 늦게 실행된 것
    if now < scheduled_today:
        target_date = now.date() - timedelta(days=1)
    else:
        target_date = now.date()

    return now, target_date


def send_discord(content):
    webhook_url = os.environ.get(
        "DISCORD_WEBHOOK_URL"
    )

    if not webhook_url:
        raise RuntimeError(
            "DISCORD_WEBHOOK_URL 환경변수가 없습니다."
        )

    payload = json.dumps(
        {
            "content": content,
            "allowed_mentions": {
                "parse": []
            }
        },
        ensure_ascii=False
    ).encode("utf-8")

    request = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "toji-reading-bot/1.0"
        },
        method="POST"
    )

    with urllib.request.urlopen(
        request,
        timeout=20
    ) as response:

        if response.status not in (
            200,
            204
        ):
            raise RuntimeError(
                f"Discord webhook 실패: "
                f"HTTP {response.status}"
            )


def main():
    if test_date:
        now = datetime.fromisoformat(
            test_date
        ).replace(
            tzinfo=KST
        )

    target_date = now.date()
    else:
        now, target_date = get_target_datetime(
            message_type
        )


    week, day_index = find_current_schedule_by_date(
        target_date
    )

    if not week:
        print(
            f"{now.date()}: "
            "독서 일정 밖의 날짜라 "
            "발송하지 않습니다."
        )
        return

    message = build_message(
        week,
        day_index,
        message_type
    )

    if "--preview" in sys.argv:
        print(message)
        return

    send_discord(message)

    print(
        f"{now.date()} "
        f"{week['week']}주차 "
        f"Day {day_index + 1} "
        f"{message_type} 발송 완료"
    )


if __name__ == "__main__":
    main()

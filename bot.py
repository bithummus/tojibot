import os
import json
import sys
import urllib.request

from datetime import datetime
from zoneinfo import ZoneInfo


ROOT = os.path.dirname(os.path.abspath(__file__))
KST = ZoneInfo("Asia/Seoul")


MORNING_CHEERS = [
    "오늘도 한 장씩 차근차근 읽어봐요. 아자아자! 📚",
    "오늘 분량은 오늘의 내가 해결한다! 천천히 시작해봐요.",
    "조금씩 읽다 보면 어느새 20권 완독! 오늘도 파이팅!",
    "부담 갖지 말고 일단 책부터 펼쳐봅시다. 오늘도 잘 읽어봐요!",
    "하루치만 읽으면 됩니다. 오늘의 『토지』도 힘차게 출발!",
    "한꺼번에 몰아 읽지 말고 오늘 몫만 착실하게! 파이팅!",
    "오늘도 『토지』 세계로 출발! 재미있게 읽고 저녁에 다시 만나요.",
    "딱 오늘 분량만 생각하기! 조금씩 꾸준히 가봅시다.",
    "벌써 여기까지 왔어요. 오늘도 흐름 끊기지 않게 이어가봐요!",
    "책 한 번 펼치기가 제일 어렵습니다. 펼쳤으면 이미 절반 성공!",
]


def load_schedule():
    path = os.path.join(ROOT, "data", "schedule.json")

    with open(path, encoding="utf-8") as f:
        return json.load(f)


def find_current_schedule(now):
    today = now.date().isoformat()

    for week in load_schedule():
        if week["start"] <= today <= week["end"]:
            start_date = datetime.fromisoformat(
                week["start"]
            ).date()

            day_index = (now.date() - start_date).days

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

오늘까지 읽으면 주간 누적 **{cumulative}/{week['pages']}쪽**이에요.

{cheer}

_오늘 분량을 조금 앞뒤로 조정해 읽어도 괜찮아요. 장이 얼마 남지 않았다면 장 끝까지 읽는 걸 추천해요._
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

오늘 분량 읽으신 분들은 편하게 한마디씩 남겨주세요.  
아직 못 읽었다면 괜찮아요. 오늘 밤 조금이라도 이어가봅시다! 📖
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
    test_date = os.environ.get("TEST_DATE")
    message_type = os.environ.get(
        "MESSAGE_TYPE",
        "evening"
    )

    if test_date:
        now = datetime.fromisoformat(
            test_date
        ).replace(
            tzinfo=KST
        )
    else:
        now = datetime.now(KST)

    week, day_index = find_current_schedule(
        now
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

import os
import re
import json
import math
import hashlib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord

ROOT = os.path.dirname(os.path.abspath(__file__))
KST = ZoneInfo("Asia/Seoul")
TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
SCHEDULE_PATH = os.path.join(ROOT, "data", "schedule.json")

if not TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN 환경변수가 없어.")


def load_schedule():
    with open(SCHEDULE_PATH, encoding="utf-8") as f:
        return json.load(f)


SCHEDULE = load_schedule()


def parse_date(value):
    return datetime.fromisoformat(value).date()


BOOK_START = parse_date(SCHEDULE[0]["start"])
BOOK_END = parse_date(SCHEDULE[-1]["end"])


def today_kst():
    return datetime.now(KST).date()


def schedule_for_date(target_date):
    iso = target_date.isoformat()
    for week in SCHEDULE:
        if week["start"] <= iso <= week["end"]:
            day_index = (target_date - parse_date(week["start"])).days
            return week, day_index
    return None, None


def week_by_number(number):
    return next((w for w in SCHEDULE if w["week"] == number), None)


def fmt_date(d):
    return f"{d.month}/{d.day}"


def fmt_week_dates(week):
    return f"{fmt_date(parse_date(week['start']))}~{fmt_date(parse_date(week['end']))}"


def weekday_name(index):
    return ["월", "화", "수", "목", "금", "토", "일"][index]


def progress_bar(done, total=7):
    done = max(0, min(total, done))
    return "█" * done + "░" * (total - done)


def stable_choice(options, key):
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return options[int.from_bytes(digest[:4], "big") % len(options)]


CHEERS = [
    "오늘 분량만 생각하자. 20권 전체를 한꺼번에 읽는 거 아니니까ㅋㅋ 📚",
    "일단 책부터 펼쳐. 5쪽 읽고 나면 의외로 그냥 계속 읽게 될지도 몰라.",
    "밀리지 않는 비결은 거창하지 않다. 오늘 몫을 오늘 읽는 것! 아자아자.",
    "조금씩 가도 계속 가면 끝난다. 오늘도 『토지』 한 걸음!",
    "책 펼치기까지가 제일 어렵지. 펼쳤으면 이미 반은 했다.",
    "오늘 목표량 보고 겁먹지 말고 10쪽씩 끊어서 가자. 생각보다 금방 간다!",
    "완독은 하루의 대단한 몰입보다 매일의 평범한 30여 쪽이 만든다. 가보자.",
    "오늘 못 읽으면 내일의 내가 두 배로 힘들다… 오늘의 내가 조금 도와주자ㅋㅋ",
    "딱 오늘치만! 다 읽고 나면 아주 당당하게 쉬자.",
    "꾸준히 읽는 사람이 결국 20권을 덮는다. 오늘도 출발!",
]

TIRED_REPLIES = [
    "그럴 수 있지ㅋㅋ 오늘 목표를 통째로 보지 말고 **10쪽만** 읽어보자. 10쪽 뒤에도 싫으면 잠깐 쉬고.",
    "오늘 유난히 안 읽히는 날이면 분량보다 흐름 안 끊는 게 더 중요해. **한 장면만 읽고 책 덮어도 출석 인정** 느낌으로 가자.",
    "30몇 쪽이 너무 커 보이면 **10쪽 + 10쪽 + 나머지**로 쪼개자. 첫 10쪽만 지금.",
    "오늘 컨디션이 별로면 완벽하게 따라잡으려 하지 말자. **조금이라도 읽어서 내일 진입 장벽을 낮추는 게 목표**!",
]

DONE_REPLIES = [
    "오 완료! 오늘 몫 끝냈으면 죄책감 없이 쉬어도 된다. 아주 잘했다 📚",
    "좋아, 오늘치 클리어. 이런 날들이 쌓여서 20권 완독이 되는 거지.",
    "멋지다ㅋㅋ 오늘은 더 욕심내도 되고 여기서 딱 멈춰도 돼. 중요한 건 오늘 목표 달성!",
    "오늘 진도 완료! 이제 다른 사람들 감상 구경하면서 한마디 던져도 좋겠다.",
]

HELLO_REPLIES = [
    "안녕! 오늘 진도 물어봐도 되고, 밀렸다고 하소연해도 되고, 그냥 응원해달라고 해도 돼ㅋㅋ",
    "왔어? 📚 오늘 어디까지 읽을지 볼까, 아니면 이번 주 진도부터 볼까?",
    "안녕! 『토지』 담당 잔소리꾼 출근했다. 오늘 진도 궁금하면 바로 물어봐.",
]

THANKS_REPLIES = [
    "별말을ㅋㅋ 우리 20권까지 같이 가자.",
    "좋지! 읽다가 또 막막해지면 바로 불러.",
    "천만에. 오늘 분량 잊지 말고 슬쩍 읽고 와 📚",
]

DEFAULT_TOPICS = [
    "오늘 읽은 범위에서 **가장 눈에 들어온 인물 한 명**만 고른다면 누구야? 왜 그 인물이었는지도 궁금해.",
    "오늘 읽으면서 **인물 사이의 관계가 미묘하게 달라졌다고 느낀 순간**이 있었어? 말 한마디나 행동 하나만 골라도 돼.",
    "오늘 부분에서 **당시의 가족·신분·사회 규범**이 지금과 가장 다르게 느껴진 장면은 뭐였어?",
    "오늘은 **공간이나 풍경**에 주목해보자. 배경이 인물의 감정이나 분위기를 더 강하게 만든 대목이 있었어?",
    "오늘 읽은 인물의 선택 중에서 **나라면 다르게 했을 것 같은 선택** 하나만 꼽아보자.",
    "오늘 읽은 부분에서 **이상하게 오래 남는 문장·장면·이미지** 하나 있었어? 정확한 문장을 옮기지 않아도 느낌만 말해도 돼.",
    "이번 주 범위를 돌아보자. **다음 주까지 기억하고 싶은 인물·사건·감정 하나**만 남긴다면 뭐야?",
]


def week_summary(week, compact=False):
    if compact:
        return (
            f"**{week['week']}주차 · {fmt_week_dates(week)}**\n"
            f"{week['volume']} · {week['scope']}\n"
            f"총 **{week['pages']}쪽**"
        )

    daily = " / ".join(f"{p}쪽" for p in week["daily_pages"])
    return (
        f"📚 **{week['week']}주차 진도 · {fmt_week_dates(week)}**\n"
        f"**범위:** {week['volume']} · {week['scope']}\n"
        f"**주간 분량:** {week['pages']}쪽\n"
        f"**하루 목표:** {daily}\n\n"
        "하루치 페이지는 균등 분배한 목표량이야. 장이 얼마 안 남았다면 몇 쪽 앞뒤로 움직여서 장 끝까지 읽어도 괜찮아."
    )


def day_summary(target_date, intro="오늘"):
    week, day = schedule_for_date(target_date)
    if not week:
        if target_date < BOOK_START:
            days = (BOOK_START - target_date).days
            return f"아직 시작 전이야! 시작일은 **{BOOK_START:%Y-%m-%d}**, 시작까지 **{days}일** 남았어."
        if target_date > BOOK_END:
            return f"우리 일정은 **{BOOK_END:%Y-%m-%d}**에 끝났어. 전20권 완독 일정 완료! 🎉"
        return "그 날짜는 일정에서 찾지 못했어."

    pages = week["daily_pages"][day]
    cumulative = sum(week["daily_pages"][:day + 1])
    return (
        f"📖 **{intro}은 {week['week']}주차 Day {day + 1} ({weekday_name(day)})**\n"
        f"**목표:** 약 **{pages}쪽**\n"
        f"**{intro}까지 주간 누적 목표:** {cumulative}/{week['pages']}쪽\n"
        f"**이번 주 전체 범위:** {week['volume']} · {week['scope']}\n\n"
        f"일일 페이지 경계는 딱 고정해둔 건 아니야. 오늘은 **약 {pages}쪽** 읽고, 장 끝이 가까우면 거기까지 가면 돼."
    )


def current_progress(target_date):
    week, day = schedule_for_date(target_date)
    if not week:
        return day_summary(target_date)

    cumulative = sum(week["daily_pages"][:day + 1])
    remaining_after_today = week["pages"] - cumulative
    remaining_days = 6 - day
    text = (
        f"지금 **{week['week']}주차 Day {day + 1}**이야.\n"
        f"{progress_bar(day + 1)} {day + 1}/7\n\n"
        f"오늘까지 목표 누적은 **{cumulative}/{week['pages']}쪽**."
    )
    if remaining_days > 0:
        text += f"\n오늘 목표까지 마쳤다고 보면 이번 주에 **{remaining_after_today}쪽**, **{remaining_days}일** 남아."
    else:
        text += "\n오늘이 이번 주 마지막 날이야. 오늘치만 끝내면 이번 주 완료!"
    return text


def remaining_book(target_date):
    week, day = schedule_for_date(target_date)
    if target_date < BOOK_START:
        return f"아직 시작 전이야. 시작일은 **{BOOK_START:%Y-%m-%d}**!"
    if target_date > BOOK_END:
        return "이미 완독 일정이 끝났어 🎉"
    if not week:
        return "현재 일정을 찾지 못했어."

    idx = week["week"] - 1
    future_pages = sum(w["pages"] for w in SCHEDULE[idx + 1:])
    today_and_after = sum(week["daily_pages"][day:])
    total_remaining = future_pages + today_and_after
    days_left = (BOOK_END - target_date).days + 1
    weeks_left = math.ceil(days_left / 7)
    return (
        f"오늘 목표부터 포함하면 완독까지 대략 **{total_remaining:,}쪽** 남았어.\n"
        f"일정상 **{days_left}일**, 약 **{weeks_left}주** 남았고 마지막 날은 **{BOOK_END:%Y-%m-%d}**야.\n\n"
        "숫자로 보면 커 보이지만 우린 하루에 30여 쪽씩만 보면 된다ㅋㅋ"
    )


def topic_for_date(target_date):
    week, day = schedule_for_date(target_date)
    if not week:
        return day_summary(target_date)

    topics = week.get("daily_topics") or []
    topic = str(topics[day]).strip() if day < len(topics) and str(topics[day]).strip() else DEFAULT_TOPICS[day]
    return (
        f"💬 **{week['week']}주차 Day {day + 1} 이야기거리**\n"
        f"{topic}\n\n"
        "정답 찾는 토론 말고, 읽으면서 받은 인상 한두 문장만 던져도 충분해."
    )


def catch_up_plan(missed_pages, target_date):
    week, day = schedule_for_date(target_date)
    if not week:
        return day_summary(target_date)

    days_left = 7 - day
    today_goal = week["daily_pages"][day]
    if missed_pages <= 0:
        return "밀린 게 0쪽이면 아주 훌륭한데?ㅋㅋ 그냥 오늘 목표대로 가면 돼."

    extra = math.ceil(missed_pages / days_left)
    if days_left >= 2:
        return (
            f"오케이, **{missed_pages}쪽 밀린 상태**로 잡아볼게.\n\n"
            f"이번 주 남은 **{days_left}일**에 나누면 하루에 원래 목표 + **약 {extra}쪽**씩 더 읽으면 따라잡을 수 있어.\n"
            f"오늘 원래 목표가 {today_goal}쪽이니까 오늘은 **약 {today_goal + extra}쪽** 정도.\n\n"
            "근데 한 번에 다 복구하려고 무리하진 말자. 밀린 분량이 크면 이번 주와 다음 주에 반씩 나눠도 돼."
        )

    return (
        f"오늘이 이번 주 마지막 날이라 **{missed_pages}쪽**을 오늘 전부 메우는 건 부담일 수 있어.\n"
        f"오늘 원래 목표 {today_goal}쪽부터 끝내고, 밀린 분량은 다음 주 4일에 나눠 하루 **{math.ceil(missed_pages / 4)}쪽 정도씩** 추가하자."
    )


def read_pages_reply(read_pages, target_date, says_week=False):
    week, day = schedule_for_date(target_date)
    if not week:
        return day_summary(target_date)

    if says_week:
        expected = sum(week["daily_pages"][:day + 1])
        remaining_total = max(0, week["pages"] - read_pages)
        diff = read_pages - expected
        if diff >= 0:
            return (
                f"이번 주에 **{read_pages}쪽** 읽었구나. 오늘까지 목표가 {expected}쪽이니까 **{diff}쪽 앞서 있어!**\n"
                f"이번 주 전체로는 **{remaining_total}쪽** 남았어. 아주 여유롭다."
            )
        return (
            f"이번 주에 **{read_pages}쪽** 읽었구나. 오늘까지 목표 {expected}쪽보다 **{-diff}쪽** 정도 뒤야.\n"
            f"그래도 이번 주 전체 남은 건 **{remaining_total}쪽**. 남은 날에 조금씩 나누면 돼."
        )

    target = week["daily_pages"][day]
    remaining = target - read_pages
    if remaining > 0:
        return (
            f"오늘 **{read_pages}쪽** 읽었네. 목표가 약 {target}쪽이니까 **{remaining}쪽 정도**만 더 읽으면 오늘치 끝!\n"
            "여기까지 읽은 김에 조금만 더 가자 📚"
        )
    if remaining == 0:
        return stable_choice(DONE_REPLIES, f"{target_date}-exact")
    return f"오늘 목표보다 **{-remaining}쪽 더 읽었어!** 오늘치는 이미 초과 달성ㅋㅋ 이쯤에서 쉬어도 돼."


def next_week_summary(target_date):
    week, _ = schedule_for_date(target_date)
    if not week:
        return day_summary(target_date)
    next_week = week_by_number(week["week"] + 1)
    if not next_week:
        return "지금이 마지막 40주차야. 다음 주 진도는 없다. 완독이다! 🎉"
    return "다음 주는 이렇게 읽어.\n\n" + week_summary(next_week, compact=True)


def previous_week_summary(target_date):
    week, _ = schedule_for_date(target_date)
    if not week:
        return day_summary(target_date)
    prev = week_by_number(week["week"] - 1)
    if not prev:
        return "지금이 1주차라 지난 주 진도는 없어."
    return "지난 주 범위는 이거였어.\n\n" + week_summary(prev, compact=True)


def weekend_plan(target_date):
    week, day = schedule_for_date(target_date)
    if not week:
        return day_summary(target_date)
    expected = sum(week["daily_pages"][:day])
    left = week["pages"] - expected
    days = 7 - day
    per_day = math.ceil(left / days)
    return (
        f"오늘부터 이번 주 끝까지 남은 계획량은 대략 **{left}쪽**이야.\n"
        f"남은 **{days}일**에 똑같이 나누면 하루 **약 {per_day}쪽**.\n"
        "주말 몰아읽기도 가능하긴 한데, 토·일에 너무 몰리면 다음 주 시작이 힘들 수 있어서 오늘 10~20쪽이라도 빼두는 걸 추천해."
    )


def help_message():
    return (
        "나한테 이런 식으로 말 걸면 돼.\n\n"
        "• `@토지봇 오늘 어디까지야?`\n"
        "• `@토지봇 이번 주 진도 알려줘`\n"
        "• `@토지봇 다음 주 뭐 읽어?`\n"
        "• `@토지봇 12주차 뭐 읽어?`\n"
        "• `@토지봇 오늘 대화거리 줘`\n"
        "• `@토지봇 나 70쪽 밀렸어`\n"
        "• `@토지봇 오늘 20쪽 읽었어`\n"
        "• `@토지봇 이번 주 100쪽 읽었어`\n"
        "• `@토지봇 주말에 몰아 읽으면?`\n"
        "• `@토지봇 완독까지 얼마나 남았어?`\n"
        "• `@토지봇 읽기 싫어`\n"
        "• `@토지봇 응원해줘`\n\n"
        "내 답변에 답글로 이어서 말할 때는, 답글이 봇 메시지를 가리키고 있으면 멘션 없이도 반응해."
    )


def clean_message(text, bot_id):
    text = re.sub(fr"<@!?{bot_id}>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_pages(text):
    m = re.search(r"(\d{1,4})\s*쪽", text)
    return int(m.group(1)) if m else None


def extract_week_number(text):
    m = re.search(r"(\d{1,2})\s*주차", text)
    if not m:
        return None
    n = int(m.group(1))
    return n if 1 <= n <= 40 else None


def reply_for(text, author_id):
    now = today_kst()
    normalized = text.lower().strip()

    if not normalized or normalized in {"야", "저기", "토지봇"}:
        return stable_choice(HELLO_REPLIES, f"{now}-{author_id}-empty")

    if any(k in normalized for k in ["도움", "사용법", "뭐 할 수", "뭐할수", "명령어"]):
        return help_message()

    if any(k in normalized for k in ["너 누구", "넌 누구", "정체가 뭐", "뭐하는 봇"]):
        return "나는 우리 『토지』 40주 완독 일정 담당 봇이야ㅋㅋ 오늘 진도, 주차별 범위, 밀린 분량 계산, 대화거리, 응원 정도는 꽤 잘해."

    if any(k in normalized for k in ["안녕", "하이", "ㅎㅇ", "반가"]):
        return stable_choice(HELLO_REPLIES, f"{now}-{author_id}-hello")

    if any(k in normalized for k in ["고마워", "고맙", "땡큐", "감사"]):
        return stable_choice(THANKS_REPLIES, f"{now}-{author_id}-thanks")

    specific_week = extract_week_number(normalized)
    if specific_week:
        return week_summary(week_by_number(specific_week))

    if "내일" in normalized:
        return day_summary(now + timedelta(days=1), "내일")
    if "어제" in normalized:
        return day_summary(now - timedelta(days=1), "어제")
    if "다음 주" in normalized or "다음주" in normalized:
        return next_week_summary(now)
    if any(k in normalized for k in ["지난 주", "지난주", "저번 주", "저번주"]):
        return previous_week_summary(now)

    if any(k in normalized for k in ["완독 언제", "끝나는 날", "마지막 날", "언제 끝"]):
        return f"완독 예정일은 **{BOOK_END:%Y-%m-%d}**야. 마지막 40주차는 {fmt_week_dates(SCHEDULE[-1])}!"

    if (("완독" in normalized and any(k in normalized for k in ["얼마나", "몇", "남"])) or ("전체" in normalized and "남" in normalized)):
        return remaining_book(now)

    pages = extract_pages(normalized)
    if pages is not None and any(k in normalized for k in ["밀렸", "밀림", "뒤처", "못 읽"]):
        return catch_up_plan(pages, now)

    if pages is not None and any(k in normalized for k in ["읽었", "읽음", "봤어", "봤다"]):
        says_week = "이번 주" in normalized or "이번주" in normalized
        return read_pages_reply(pages, now, says_week)

    if any(k in normalized for k in ["읽기 싫", "못 읽겠", "귀찮", "힘들", "지쳤", "막막"]):
        return stable_choice(TIRED_REPLIES, f"{now}-{author_id}-tired")

    if any(k in normalized for k in ["다 읽었", "오늘치 끝", "오늘 거 끝", "완료했", "끝냈"]):
        return stable_choice(DONE_REPLIES, f"{now}-{author_id}-done")

    if any(k in normalized for k in ["응원", "파이팅", "화이팅", "힘내라고", "잔소리"]):
        week, day = schedule_for_date(now)
        prefix = f"오늘 목표는 **약 {week['daily_pages'][day]}쪽**. " if week else ""
        return prefix + stable_choice(CHEERS, f"{now}-{author_id}-cheer")

    if any(k in normalized for k in ["대화거리", "이야기거리", "토론거리", "질문 줘", "질문줘", "얘기할 거", "얘기할거"]):
        return topic_for_date(now)

    if any(k in normalized for k in ["주말에 몰아", "몰아 읽", "몰아읽"]):
        return weekend_plan(now)

    if any(k in normalized for k in ["몇 쪽 남", "얼마나 남", "진행률", "진도율", "지금 어디쯤"]):
        return current_progress(now)

    if "몇 주차" in normalized or "몇주차" in normalized:
        week, day = schedule_for_date(now)
        if not week:
            return day_summary(now)
        return f"지금 **{week['week']}주차 Day {day + 1} ({weekday_name(day)})**야.\n{fmt_week_dates(week)} · 총 {week['pages']}쪽"

    if "이번 주" in normalized or "이번주" in normalized:
        week, _ = schedule_for_date(now)
        return week_summary(week) if week else day_summary(now)

    if any(k in normalized for k in ["오늘", "어디까지", "몇 쪽", "몇쪽", "뭐 읽", "뭘 읽"]):
        return day_summary(now)

    if any(k in normalized for k in ["ㅋㅋ", "ㅎㅎ"]):
        return "ㅋㅋ 책 얘기하러 불렀으면 오늘 진도도 슬쩍 확인하고 가자. `오늘 어디까지야?`라고 물어봐."

    return (
        "무슨 말인지는 대충 알 것 같은데 아직 거기까지는 못 배웠어ㅋㅋ\n\n"
        "대신 **오늘 진도 / 이번 주 진도 / 특정 주차 / 밀린 분량 / 읽은 분량 / 대화거리 / 응원 / 완독까지 남은 분량**은 대답할 수 있어.\n"
        "`@토지봇 도움말`이라고 해보면 예시를 보여줄게."
    )


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(
    intents=intents,
    allowed_mentions=discord.AllowedMentions.none(),
)


def is_reply_to_me(message):
    if not message.reference or not message.reference.resolved:
        return False
    resolved = message.reference.resolved
    return isinstance(resolved, discord.Message) and client.user is not None and resolved.author.id == client.user.id


@client.event
async def on_ready():
    print(f"로그인 완료: {client.user} ({client.user.id})")
    await client.change_presence(activity=discord.Game("『토지』 40주 완독 중 📚"))


@client.event
async def on_message(message):
    if message.author.bot or client.user is None:
        return

    mentioned = client.user in message.mentions
    replying = is_reply_to_me(message)
    if not mentioned and not replying:
        return

    text = clean_message(message.content, client.user.id)
    try:
        response = reply_for(text, message.author.id)
        await message.reply(response, mention_author=False)
    except Exception as e:
        print(f"메시지 처리 오류: {e!r}")
        await message.reply("앗, 방금 계산하다가 꼬였어. 잠깐 뒤에 한 번만 다시 불러줘!", mention_author=False)


client.run(TOKEN)

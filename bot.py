import os,json,sys,urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
ROOT=os.path.dirname(os.path.abspath(__file__))
KST=ZoneInfo("Asia/Seoul")
def data():
    return json.load(open(os.path.join(ROOT,"data","schedule.json"),encoding="utf-8"))
def current(now):
    t=now.date().isoformat()
    for w in data():
        if w["start"]<=t<=w["end"]:
            d=(now.date()-datetime.fromisoformat(w["start"]).date()).days
            return w,d
    return None,None
def message(w,d):
    cum=sum(w["daily_pages"][:d+1]); bar="█"*(d+1)+"░"*(6-d)
    wd=["월","화","수","목","금","토","일"][d]
    return f"""📖 **박경리 『토지』 {w['week']}주차 · Day {d+1} ({wd})**
**이번 주 범위**: {w['volume']} · {w['scope']}
**오늘 목표**: 약 {w['daily_pages'][d]}쪽 · 주간 누적 {cum}/{w['pages']}쪽
**진행도**: {bar} {d+1}/7

💬 **오늘의 짧은 이야기**
{w['daily_topics'][d]}

_주간 분량을 7일에 고르게 나눈 목표치예요. 장 끝이 가까우면 몇 쪽 앞뒤로 조정해도 됩니다._"""
def send(msg):
    url=os.environ["DISCORD_WEBHOOK_URL"]
    body=json.dumps({"content":msg,"username":"토지 완독 도우미","allowed_mentions":{"parse":[]}},ensure_ascii=False).encode()
    req=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json","User-Agent":"toji-reading-bot/1.0"},method="POST")
    urllib.request.urlopen(req,timeout=20).read()
def main():
    test=os.getenv("TEST_DATE")
    now=datetime.fromisoformat(test).replace(tzinfo=KST) if test else datetime.now(KST)
    w,d=current(now)
    if not w: print("독서 일정 밖의 날짜입니다."); return
    msg=message(w,d)
    if "--preview" in sys.argv: print(msg)
    else: send(msg); print("발송 완료")
if __name__=="__main__": main()

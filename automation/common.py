import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
MAIL_TO = os.environ["MAIL_TO"]

BRAND_CONTEXT = """
アカウント名・発信者ペルソナ:「サカキ」(表示名「サカキ｜本質のAI活用術」)
商品名:「本質のAI活用術ー自分の"分身"を働かせるという考え方」(note、6,800円)
ターゲット読者:AI初心者の会社員・個人事業主。日々の定型業務(勤怠管理・メール対応・資料作成など)に時間を取られている人
核となる主張:AI活用の本質は「頼む」ことではなく「自分の判断基準を言語化してAIに移植し、分身として働かせる」こと
独自フレームワーク「分身メソッド」4ステップ:①言語化(自分の判断基準を掘り出す)②権限設計(どこまで任せるか線引き)③仕組み化(実際に動く形に落とし込む)④検証ループ(運用しながら基準を更新し続ける)
著者の実務背景:勤怠表作成、メール仕分け管理、Excel VBA作成、業務アプリ作成、AI自動化による業務委託
トーン:誠実、煽らない。「本質」を連呼せず、内容で語る。実在しない具体的な実績数字を捏造しない。特定の実在人物を名指しで断定的に引用しない
"""


def send_mail(subject: str, body: str, attachment_path: Path | None = None) -> None:
    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = MAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    if attachment_path is not None:
        with open(attachment_path, "rb") as f:
            img = MIMEImage(f.read(), name=attachment_path.name)
        msg.attach(img)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, [MAIL_TO], msg.as_string())

import os
import pandas as pd
import urllib.request
from pythonosc import udp_client
from pythonosc.osc_message_builder import OscMessageBuilder
from pathlib import Path
import time

cover_art_list = pd.read_csv("cover_art.csv")
os.makedirs("./cover_art", exist_ok=True)

def send_osc(content):
    # UDPのクライアントを作る
    client = udp_client.UDPClient("127.0.0.1", 6666)

    # 送信するメッセージを作って送信する eg. address = '/loops'
    msg = OscMessageBuilder(address="/cover_art")
    msg.add_arg(content)
    m = msg.build()

    client.send(m)

def cover_art_dawnloader():
    for cover_art_url, track_title, uri in zip(cover_art_list["cover_art"],cover_art_list["title"], cover_art_list["uri"]):
        #保存パスの設定
        artwork_path = f"./cover_art/{uri}.jpeg"
        #カバーアートのダウンロード
        urllib.request.urlretrieve(cover_art_url, artwork_path)

        current_dir = Path.cwd()
        artwork_abs_path = current_dir.joinpath(f"cover_art/{uri}.jpeg")

        # osc送信
        send_osc(str(artwork_abs_path))
        print(f"{track_title} sended!")

        #10秒停止
        time.sleep(10)

if __name__=="__main__":
    cover_art_dawnloader()






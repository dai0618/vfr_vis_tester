"""
Open Sound Control Server/Client and callback function design example.

2022-11-11
Atsuya Kobayashi
"""
import os
import threading
from typing import Any, Callable, Dict, List, Optional, Union

from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

import urllib.request
from pathlib import Path


class OSCServer:
    def __init__(self, ip: str, port: int) -> None:
        # addresses
        self.address = "/cover_art"
        self.address_hoge = "/example_hoge"
        self.address_fuga = "/example_fuga"
        self.address_piyo = "/example_piyo"
        # callback functions
        self.on_received: Optional[Callable] = None
        self.on_received_hoge: Optional[Callable] = None
        self.on_received_fuga: Optional[Callable] = None
        self.on_received_piyo: Optional[Callable] = None
        self.server: Optional[BlockingOSCUDPServer] = None
        self.ip = ip
        self.port = port

    def parse_message(self, input_args: str) -> List[str]:
        if type(input_args) == float:
            args = [input_args]
        else:
            args: List[str] = input_args.split(" ")
        return args

    def run(self, single_thread=False) -> None:
        """Start OSC server on main or sub thread.

        Args:
            single_thread (bool, optional): Defaults to False.
        """
        self.dispatcher = Dispatcher()

        if self.on_received:
            self.dispatcher.map(self.address,
                                self.on_received)  # type: ignore
        # NOTE: 受け付けるアドレスを増やしたい場合は以下のようにしてアドレスを増やす
        if self.on_received_hoge:
            self.dispatcher.map(self.address_hoge,
                                self.on_received_hoge)  # type: ignore
        if self.on_received_fuga:
            self.dispatcher.map(self.address_fuga,
                                self.on_received_fuga)  # type: ignore
        if self.on_received_piyo:
            self.dispatcher.map(self.address_piyo,
                                self.on_received_piyo)  # type: ignore

        self.server = BlockingOSCUDPServer(
            (self.ip, self.port), self.dispatcher)
        print(f"Serving on {self.server.server_address}")
        if single_thread:
            self.server.serve_forever()
        else:
            # running the server on new thread
            server_thread = threading.Thread(target=self.server.serve_forever)
            server_thread.start()

    def stop(self):
        if self.server is not None:
            self.server.shutdown()

    def __del__(self):
        if self.server is not None:
            self.server.shutdown()


class OSCSender:
    def __init__(self, ip: str, port: int) -> None:
        self.client = udp_client.SimpleUDPClient(ip, port)
        # NOTE: 一つのSenderに付き送れるホストは一つ。
        self.ip = ip
        self.port = port

    def send(self, path: str, msg: Any) -> None:
        assert path[0] == "/", "given osc address path is incorrect"
        print(f"sending OSC message",
              f"(type={type(msg)})",
              f"to {self.ip}:{self.port}:{path}")
        self.client.send_message(path, msg)

    def __del__(self):
        if self.client is not None:
            del self.client


def get_sample_callback(
    sender: OSCSender,
    keyword: str = "",
    # given_path: str = ""
) -> Callable:
    """Callback関数を返す関数

    Args:
        sender (OSCSender): 受信時にオウム返しをするのでClientのインスタンスが必要
        keyword (str, optional): hoge/fuga/piyo 等のアドレスのときどうするかみたいな.

    Returns:
        Callable: 関数を返す
    """

    # NOTE: もし機械学習モデル等を読む場合は、`get_sample_callback`の引数でパスを受け取り
    # ここでインスタンスの読み込みを行うことで、毎回の呼び出しでの読み込みなどが発生せずに済む
    # 例) model = Model.load_model(given_path)

    cover_art_folder = "./cover_art"
    os.makedirs(cover_art_folder, exist_ok=True)

    def callback_func(addr: str, *args: Any):
        """Actual callback function: 実際にOSCを受け取って呼ばれる関数

        Args:
            addr (str): OSCのパス (e.g. /path/to)
            args (Any): 可変長引数なのでTupleとして扱うこと
        """

        # NOTE: ここで処理を行う。
        # 例) res = model.generate(type=args[0])
        #     res.save_image("/generated/path.png")
        #     sender.send("/generated_result", "/generated/path.png")
        for i in range(0,8):
            if args[1] == i+1:
                vis_addr = f"/cover_art_path{str(args[1])}"
                #保存パスの設定
                artwork_path = f"./cover_art/{args[2]}.jpeg"
                #カバーアートのダウンロード
                urllib.request.urlretrieve(args[0], artwork_path)

                current_dir = Path.cwd()
                cover_abs_path = current_dir.joinpath(f"cover_art/{args[2]}.jpeg")

                sender.send(vis_addr, str(cover_abs_path))  # parrot return
                print(vis_addr, str(cover_abs_path))
    return callback_func


if __name__ == "__main__":
    server = OSCServer("127.0.0.1", 7777)
    sender = OSCSender("127.0.0.1", 6666)
    server.on_received = get_sample_callback(sender)
    # NOTE: 別のcallbackを用意しても良い
    # server.on_received_hoge = get_sample_callback(sender, "hoge")
    # server.on_received_fuga = get_sample_callback(sender, "fuga")
    # server.on_received_piyo = get_sample_callback(sender, "piyo")
    server.run(single_thread=True)
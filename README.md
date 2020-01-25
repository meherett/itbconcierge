ITBトークンとは
=============

ITBトークンとは、IT分科会を主体とし発行されたトークンのことです。
トークンエコノミーの実現を最終的な目的とし、
まずは身近なところからトークンの活用を模索してまいります。

現在ITBトークンはEthereumのTestnet(Ropsten)上のトークンとして発行されています。
Testnet(Ropsten)にアクセス可能なEthWalletであればITBトークンを自由に送受金することができます。

### ITBトークンの基本情報

項目 | 説明
------------- | -------------
ネットワーク | Testnet(Ropsten)
シンボル | ITB/ITB
コントラクトアドレス | 0x1d5406ffebfd89110310a111bb02e79b9f96f7a0

### ITBトークンの利用方法

ITBトークンは、EthereumのTestnet(Ropsten)に
アクセス可能なウォレットから利用することができます。

PCではChrome拡張のMetaMask、AndroidではアプリのMetaMask、
iPhoneではアプリのMEConnectなどのウォレットから利用できます。

ただし、後に述べるITBコンシェルジュサービスを通じて、
SlackからもITBトークンを利用することができるので、
これらウォレットのインストールは必須ではありません。

### ITBトークンの入手方法

ITBトークンは、ITBコンシェルジュを呼び出し、
ユーザー登録することで入手することができます。
新規登録時にITB財団から1000ITBが付与されます。

### いいね！チップの送金

ITBトークンは、Slackで「いいね！」アイコンを送ることで、
「いいね！」をした相手に30ITBを送ることができます。

また、「いいね！」をした方・された方の"両者"に、
ITB財団から50ITBずつ新規に割り当てが行われます。

ITB財団はWin-Winの良好なコミュニケーションを促進します。

### ITB Cafeでお菓子を購入する

ITBトークンは、ITB Cafeでお菓子と交換することができます。

現在、ITB Cafeは有志によって運営されていますが、
ITBトークンを保有・消費できるということは、
その源泉であるSlackでのコミュニケーションを通じて、
円滑なコミュニケーションが達成された成果でもあるので、

ゆくゆくは消費されたITBトークンを事業主に買い取って頂き、
ITB Cafeの運営資金にあてることで、持続可能な運営体制を整えてまいります。

また現在、ITB Cafeの支払い方法は非常に古典的でありますが、
「"Blockchain" x "IoT" x "AI"」を真に融合し、
継続的なアップデートによりハイテク化を進めてまいります。

具体的に、
(AI)顔でユーザーを認識し、
(BC)ウォレットを解錠、代金を支払いし、
(IoT)商品のロックを解除する
といった仕組みを目指します。

ITBコンシェルジュサービスとは
=============

ITBコンシェルジュサービスとは、ITBトークンの利用を総合的にサポートするためのサービスです。
Slackから呼び出して利用することができ、
ユーザーのウォレット管理から、コインの送受金までをサポートします。

使い方について
-------------

ITBコンシェルジュサービスを利用するには、
ITBコンシェルジュが参加しているSlackチャンネルか、
ITBコンシェルジュとのDMチャンネルでコマンドを投稿します。
どのようなコマンドが使用できるかは「ITB ヘルプ」と投稿することで確認できます。

ITBコンシェルジュの開発について
=============

開発環境の構築
-------------

### Pythonのバージョンを確認する

※Python3.7以上で動作します。

$ python -V
Python 3.7.4

### プロジェクトディレクトリを作成する

$ mkdir -p ~/source/itbconcierge/

### Python仮想環境を構築する

$ cd ~/source/itbconcierge/
$ mkdir .venv
$ cd ~/source/itbconcierge/.venv/
$ python3.7 -m venv py374
$ source py374/bin/activate
$ pip install --upgrade pip setuptools
$ python --version
Python 3.7.4

### ITBConciergeをインストールする

$ cd ~/source/itbconcierge/
$ python setup.py develop

Slackでボットを作成する
-------------

Slackでボットを新規作成し、発行されたAPIトークンを
slackbot_settings.pyのAPI_TOKENに記述します。

また、本機能を利用するチャンネルにボットを招待してください。

コンシェルジュを実行する
-------------

### 単体で実行する場合
$ cd ~/source/itbconcierge
$ source .venv/py374/bin/activate
$ python run.py

### supervisor化して実行する場合

supervisorをインストール
$ sudo apt -y install supervisor

サービスを定義する

```
/etc/supervisor/conf.d$ cat itbconcierge.conf 
[program:itbconcierge]
command=sudo /home/pi/source/itbconcierge/.venv/py374/bin/python /home/pi/source/itbconcierge/run.py
user=pi
autostart=true
autorestart=true
directory=/home/pi/source/itbconcierge
```

```
proxy環境下では下記をコマンド先頭に付ける必要があるかもしれない。
$ env https_proxy=xxx.xxx.xx.xxx:xxxx
```

設定ファイルを再び読み込む
$ sudo supervisorctl update

サービスを開始する
$ sudo supervisorctl start itbconcierge


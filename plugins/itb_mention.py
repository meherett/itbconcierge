import random
import re
import subprocess
from datetime import datetime, timedelta
from decimal import Decimal
from time import sleep

from slackbot.bot import default_reply, listen_to, react_to, respond_to
from slackbot.dispatcher import Message
from sqlalchemy.sql.functions import func

from slackbot_settings import (GOOD_REACTIONS, ITB_FOUNDATION_ADDRESS,
                               ITB_FOUNDATION_PRIVKEY, ITBCAFE_GOODS)

from .model import DBContext, Symbol, Users
from .wallet import Wallet

# いいね！を欲した者
greedies = []


@listen_to("ITB.*ヘルプ", re.IGNORECASE)
@respond_to("ITB.*ヘルプ", re.IGNORECASE)
def itb_get_help(message: Message):

    response_txt = "```\n"
    response_txt += "ITB ヘルプ\n"
    response_txt += "    ITBコンシェルジュサービスで利用できるコマンドと説明を表示します。\n"
    response_txt += "\n"
    response_txt += "ITB 入会\n"
    response_txt += "    ITBコンシェルジュサービスに入会します。\n"
    response_txt += "    入会するとETHアドレスが新規発行され、ITBトークンを利用できるようになります。\n"
    response_txt += "    新規発行されたETHアドレスと秘密鍵は、入会したユーザーにDMで通知します。\n"
    response_txt += "    サービスの提供のため、このアドレスの秘密鍵はコンシェルジュでもお預かりします。\n"
    response_txt += "\n"
    response_txt += "ITB 退会\n"
    response_txt += "    ITBコンシェルジュサービスを退会します。\n"
    response_txt += "\n"
    response_txt += "ITB 残高照会\n"
    response_txt += "    ITBトークンの残高を取得します。\n"
    response_txt += "\n"
    response_txt += "ITBCafe 商品一覧\n"
    response_txt += "    ITBCafeで購入できる商品一覧を取得します。\n"
    response_txt += "\n"
    response_txt += "ITBCafe 購入 {商品名}\n"
    response_txt += "    ITBCafeで商品を購入します。\n"
    response_txt += "```"

    message.reply(response_txt)


def get_user(db_context, userid: str) -> Users:
    """
    ユーザー情報を取得します。

    Parameters
    ----------
    db_context:
        DBセッション
    userid: str
        ユーザーID

    Returns
    -------
    Users
        ユーザー情報
    """

    # ユーザーIDを照会する
    user = db_context.session.query(Users) \
        .filter(Users.userid == userid) \
        .first()

    return user


@respond_to("ITB.*入会", re.IGNORECASE)
@listen_to("ITB.*入会", re.IGNORECASE)
def itb_regist_user(message: Message):

    # DBセッションを開く
    db_context = DBContext()

    # ユーザーを照会する
    userid = message.user["id"]
    user = get_user(db_context, userid)

    # ユーザー登録されている場合
    if user is not None:

        response_txt = "既にITBコンシェルジュサービスに入会しています。"
        message.reply(response_txt)

        response_txt = "あなたのアカウント情報はこちらです。\n"
        response_txt += "```\n"
        response_txt += "userid:{}\n"
        response_txt += "address:{}\n"
        response_txt += "privkey:{}\n"
        response_txt += "```"

        response_txt = response_txt.format(
            user.userid, user.address, user.privkey
        )

        message.direct_reply(response_txt)

    # ユーザー登録されていない場合
    else:

        # 新規アドレスを発行する
        new_address, new_privkey = Wallet.create_address()

        # 新規アドレスに初期残高を付与する
        faunder_wallet = Wallet(ITB_FOUNDATION_ADDRESS, ITB_FOUNDATION_PRIVKEY)
        faunder_wallet.send_to(new_address, Symbol.ETH, Decimal("1"))    # 送金時のガス代として
        faunder_wallet.send_to(new_address, Symbol.ITB, Decimal("1000"))

        # ユーザーを新規登録する
        new_user = Users(
            userid=userid,
            address=new_address,
            privkey=new_privkey,
            created_at=func.now()
        )
        db_context.session.add(new_user)
        db_context.session.flush()
        db_context.session.commit()

        response_txt = "ITBコンシェルジュサービスへ入会しました。"
        message.reply(response_txt)

        response_txt = "あなたのアカウント情報はこちらです。\n"
        response_txt += "```\n"
        response_txt += "userid:{}\n"
        response_txt += "address:{}\n"
        response_txt += "privkey:{}\n"
        response_txt += "```"

        response_txt = response_txt.format(
            userid, new_address, new_privkey
        )

        message.direct_reply(response_txt)

    # DBセッションを閉じる
    db_context.session.close()


@respond_to("ITB.*退会", re.IGNORECASE)
@listen_to("ITB.*退会", re.IGNORECASE)
def itb_cancel_registration(message: Message):

    # DBセッションを開く
    db_context = DBContext()

    # ユーザーを照会する
    userid = message.user["id"]
    user = get_user(db_context, userid)

    # ユーザー登録されていない場合
    if user is None:

        response_txt = "ITBコンシェルジュサービスを利用するには入会する必要があります。"
        message.reply(response_txt)

    # ユーザー登録されている場合
    else:

        response_txt = "退会するなんてとんでもない！"
        message.reply(response_txt)

    # DBセッションを閉じる
    db_context.session.close()


@listen_to("ITB.*残高照会", re.IGNORECASE)
@respond_to("ITB.*残高照会", re.IGNORECASE)
def itb_get_balance(message: Message):

    # DBセッションを開く
    db_context = DBContext()

    # ユーザーを照会する
    userid = message.user["id"]
    user = get_user(db_context, userid)

    # ユーザー登録されていない場合
    if user is None:

        response_txt = "ITBコンシェルジュサービスを利用するには入会する必要があります。"
        message.reply(response_txt)

    # ユーザー登録されている場合
    else:

        user_wallet = Wallet(user.address, user.privkey)
        itb_balance = user_wallet.get_balance(Symbol.ITB)

        response_txt = "ITBトークンの残高は「{} ITB」です。"

        response_txt = response_txt.format(
            itb_balance
        )

        message.reply(response_txt)

    # DBセッションを閉じる
    db_context.session.close()


@react_to(".*", re.IGNORECASE)
def itb_do_reaction(message: Message):

    # DBセッションを開く
    db_context = DBContext()

    # 送金元ユーザーを照会する
    from_userid = message.user["id"]
    from_user = get_user(db_context, from_userid)

    # 送金先ユーザーを照会する
    to_userid = message.body["item_user"]
    to_user = get_user(db_context, to_userid)

    # いずれのユーザーも登録されている場合
    if from_user and to_user:

        if message.body["reaction"] in GOOD_REACTIONS:

            try:
                # いいね！チップを送金する
                from_user_wallet = Wallet(from_user.address, from_user.privkey)
                from_user_wallet.send_to(to_user.address, Symbol.ITB, Decimal("30"))

                response_txt = "いいね！チップを送金しました。(-30 ITB)"
                message.direct_reply(response_txt)

                # いいね！報酬を付与する
                faunder_wallet = Wallet(ITB_FOUNDATION_ADDRESS, ITB_FOUNDATION_PRIVKEY)
                faunder_wallet.send_to(from_user.address, Symbol.ITB, Decimal("50"))
                faunder_wallet.send_to(to_user.address, Symbol.ITB, Decimal("50"))

                response_txt = "グッドコミュニケーションボーナス:+1:。(+50 ITB)"
                message.direct_reply(response_txt)

            except Exception as ex:
                response_txt = str(ex)

    # DBセッションを閉じる
    db_context.session.close()


@listen_to("ITBCafe.*商品一覧", re.IGNORECASE)
@respond_to("ITBCafe.*商品一覧", re.IGNORECASE)
def itbcafe_get_goods(message: Message):

    # DBセッションを開く
    db_context = DBContext()

    # ユーザーを照会する
    userid = message.user["id"]
    user = get_user(db_context, userid)

    # ユーザー登録されていない場合
    if user is None:

        response_txt = "ITBコンシェルジュサービスを利用するには入会する必要があります。"
        message.reply(response_txt)

    # ユーザー登録されている場合
    else:

        response_txt = "ITBCafeでは下記の商品を取り扱っています。\n"
        response_txt += "```\n"
        response_txt += "お菓子\n"
        response_txt += "いいね！ブースト\n"
        response_txt += "```"

        message.reply(response_txt)

    # DBセッションを閉じる
    db_context.session.close()


@listen_to("ITBCafe.*購入", re.IGNORECASE)
@respond_to("ITBCafe.*購入", re.IGNORECASE)
def itbcafe_buy_goods(message: Message):

    # DBセッションを開く
    db_context = DBContext()

    # ユーザーを照会する
    userid = message.user["id"]
    user = get_user(db_context, userid)

    # ユーザー登録されていない場合
    if user is None:

        response_txt = "ITBコンシェルジュサービスを利用するには入会する必要があります。"
        message.reply(response_txt)

    # ユーザー登録されている場合
    else:

        can_buy = False

        for goods in ITBCAFE_GOODS:

            # メッセージ本文を取得する
            message_body = message.body["text"]

            # メッセージ本文に商品に商品名が含まれている場合
            if message_body.find(goods["name"]) > -1:

                can_buy = True

                try:
                    user_wallet = Wallet(user.address, user.privkey)
                    user_wallet.send_to(ITB_FOUNDATION_ADDRESS, Symbol.ITB, Decimal(goods["price"]))

                    response_txt = "{}の購入が完了しました。(-{} ITB)"

                    response_txt = response_txt.format(
                        goods["name"], goods["price"]
                    )

                    message.reply(response_txt)

                    # いいね！を欲した者に登録する
                    if goods["name"].find("いいね") > -1:
                        add_to_greedies(message.user["id"])

                except Exception as ex:
                    response_txt = str(ex)

        if not can_buy:

            response_txt = "取り扱いのない商品です。"
            message.reply(response_txt)

    # DBセッションを閉じる
    db_context.session.close()


def add_to_greedies(userid: str):
    """
    「いいね！」を欲した人に登録する
    """
    user = list(filter(lambda x: x == userid, greedies))
    if len(user) == 0:
        greedies.append(userid)


def give_like_to_greedies(message: Message):
    """
    「いいね！」を欲した人に「いいね！」する
    """
    user = list(filter(lambda x: x == message.user["id"], greedies))
    if len(user) > 0:
        message.react(random.choice(GOOD_REACTIONS))


@listen_to(".*")
@respond_to(".*")
def default_reply_all(message: Message):
    """
    デフォルト
    """

    # 「いいね！」を欲した人に「いいね！」する
    give_like_to_greedies(message)

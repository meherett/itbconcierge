import random
import re
from decimal import Decimal

from slackbot.bot import default_reply, listen_to, react_to, respond_to
from slackbot.dispatcher import Message
from sqlalchemy.sql.functions import func

from slackbot_settings import (GOOD_REACTIONS, ITB_FOUNDATION_ADDRESS,
                               ITB_FOUNDATION_PRIVKEY, ITBCAFE_GOODS)

from .model import DBContext, Symbol, User
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


def get_user(db_context, slack_uid: str) -> User:
    """
    ユーザー情報を取得します。

    Parameters
    ----------
    db_context:
        DBセッション
    slack_uid: str
        SlackのユーザーID

    Returns
    -------
    User
        ユーザー情報
    """

    # ユーザーを照会する
    user = db_context.session.query(User) \
        .filter(User.slack_uid == slack_uid) \
        .first()

    return user


@respond_to("ITB.*入会", re.IGNORECASE)
@listen_to("ITB.*入会", re.IGNORECASE)
def itb_regist_user(message: Message):

    # DBセッションを開く
    db_context = DBContext()

    # ユーザーを照会する
    slack_uid = message.user["id"]
    user = get_user(db_context, slack_uid)

    # ユーザー登録されている場合
    if user is not None:

        response_txt = "既にITBコンシェルジュサービスに入会しています。"
        message.reply(response_txt)

        response_txt = "あなたのアカウント情報はこちらです。\n"
        response_txt += "```\n"
        response_txt += "slack_uid:{}\n"
        response_txt += "eth_address:{}\n"
        response_txt += "eth_privkey:{}\n"
        response_txt += "```"

        response_txt = response_txt.format(
            user.slack_uid, user.eth_address, user.eth_privkey
        )

        message.direct_reply(response_txt)

    # ユーザー登録されていない場合
    else:

        # ユーザーを新規登録する
        user = User(
            slack_uid=slack_uid,
            created_at=func.now()
        )
        db_context.session.add(user)
        db_context.session.flush()

        # 新規アドレスを発行する
        eth_address, eth_privkey = Wallet.create_address(user.id)
        user.eth_address = eth_address
        user.eth_privkey = eth_privkey

        # 新規アドレスに初期残高を付与する
        faunder_wallet = Wallet(ITB_FOUNDATION_ADDRESS, ITB_FOUNDATION_PRIVKEY)
        faunder_wallet.send_to(user.eth_address, Symbol.ETH, Decimal("1"))      # 送金時のガス代
        faunder_wallet.send_to(user.eth_address, Symbol.ITB, Decimal("1000"))   # 新規登録ボーナス

        db_context.session.commit()

        response_txt = "ITBコンシェルジュサービスへ入会しました。"
        message.reply(response_txt)

        response_txt = "あなたのアカウント情報はこちらです。\n"
        response_txt += "```\n"
        response_txt += "slack_uid:{}\n"
        response_txt += "eth_address:{}\n"
        response_txt += "eth_privkey:{}\n"
        response_txt += "```"

        response_txt = response_txt.format(
            slack_uid, eth_address, eth_privkey
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
    slack_uid = message.user["id"]
    user = get_user(db_context, slack_uid)

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
    slack_uid = message.user["id"]
    user = get_user(db_context, slack_uid)

    # ユーザー登録されていない場合
    if user is None:

        response_txt = "ITBコンシェルジュサービスを利用するには入会する必要があります。"
        message.reply(response_txt)

    # ユーザー登録されている場合
    else:

        user_wallet = Wallet(user.eth_address, user.eth_privkey)
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
    from_slack_uid = message.user["id"]
    from_user = get_user(db_context, from_slack_uid)

    # 送金先ユーザーを照会する
    to_slack_uid = message.body["item_user"]
    to_user = get_user(db_context, to_slack_uid)

    # いずれのユーザーも登録されている場合
    if from_user and to_user:

        if message.body["reaction"] in GOOD_REACTIONS:

            try:
                # いいね！チップを送金する
                from_user_wallet = Wallet(from_user.eth_address, from_user.privkey)
                from_user_wallet.send_to(to_user.eth_address, Symbol.ITB, Decimal("30"))

                response_txt = "いいね！チップを送金しました。(-30 ITB)"
                message.direct_reply(response_txt)

                # いいね！ボーナスを付与する
                faunder_wallet = Wallet(ITB_FOUNDATION_ADDRESS, ITB_FOUNDATION_PRIVKEY)
                faunder_wallet.send_to(from_user.eth_address, Symbol.ITB, Decimal("50"))
                faunder_wallet.send_to(to_user.eth_address, Symbol.ITB, Decimal("50"))

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
    slack_uid = message.user["id"]
    user = get_user(db_context, slack_uid)

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
    slack_uid = message.user["id"]
    user = get_user(db_context, slack_uid)

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
                    user_wallet = Wallet(user.eth_address, user.eth_privkey)
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

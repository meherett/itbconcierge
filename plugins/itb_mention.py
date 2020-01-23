import re
import subprocess
from datetime import datetime, timedelta
from decimal import Decimal
from time import sleep

from slackbot.bot import default_reply, listen_to, react_to, respond_to
from slackbot.dispatcher import Message
from sqlalchemy.sql.functions import func

from slackbot_settings import ITB_FOUNDATION_ADDRESS, ITB_FOUNDATION_PRIVKEY

from .model import DBContext, Users, Symbol
from .wallet import Wallet


@listen_to("ITB.*ヘルプ", re.IGNORECASE)
@respond_to("ITB.*ヘルプ", re.IGNORECASE)
def itb_get_help(message: Message):

    response_txt = "```\n"
    response_txt += "ITB ヘルプ\n"
    response_txt += "    ITBコンシェルジュサービスで利用できるコマンドと説明を表示します。\n"
    response_txt += "\n"
    response_txt += "ITB 入会\n"
    response_txt += "    ITBコンシェルジュサービスに入会します。\n"
    response_txt += "    入会すると、ETHアドレスが新規発行され、ITBトークンを利用することができるようになります。\n"
    response_txt += "    発行されたETHアドレスと秘密鍵はユーザーに所属し、DMで通知されます。\n"
    response_txt += "    通知された秘密鍵を外部ウォレット(MetaMaskなど)にインポートし、\n"
    response_txt += "    ITBコンシェルジュ以外の方法で、ITBトークンにアクセスすることもできます。\n"
    response_txt += "\n"
    response_txt += "ITB 残高照会\n"
    response_txt += "    ITBトークンの残高を取得します。\n"
    response_txt += "\n"
    response_txt += "ITBCafe 購入\n"
    response_txt += "    ITBCafeで商品を購入するときに実行します。\n"
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

        response_txt = "ITBコンシェルジュサービスに既に入会しています。\n"
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
        faunder_wallet.sendto(new_address, Symbol.ETH, Decimal("1"))    # 送金時のガス代として
        faunder_wallet.sendto(new_address, Symbol.ITB, Decimal("1000"))

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

        response_txt = "ITBコンシェルジュサービスへ入会しました。\n"
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
        message.direct_reply(response_txt)

    # ユーザー登録されている場合
    else:

        user_wallet = Wallet(user.address, user.privkey)
        itb_balance = user_wallet.get_balance(Symbol.ITB)

        response_txt = "ITBトークンの残高は「{} ITB」です。"

        response_txt = response_txt.format(
            itb_balance
        )

        message.direct_reply(response_txt)

    # DBセッションを閉じる
    db_context.session.close()


@listen_to(u"ITBCafe.*購入", re.IGNORECASE)
@respond_to(u"ITBCafe.*購入", re.IGNORECASE)
def itbcafe_buy_something(message: Message):

    # DBセッションを開く
    db_context = DBContext()

    # ユーザーを照会する
    userid = message.user["id"]
    user = get_user(db_context, userid)

    # ユーザー登録されていない場合
    if user is None:

        response_txt = "ITBコンシェルジュサービスを利用するには入会する必要があります。"
        message.direct_reply(response_txt)

    # ユーザー登録されている場合
    else:

        try:
            user_wallet = Wallet(user.address, user.privkey)
            user_wallet.sendto(ITB_FOUNDATION_ADDRESS, Symbol.ITB, Decimal("100"))
            response_txt = "somethingの購入が完了しました。"
        except Exception as ex:
            response_txt = str(ex)

        message.direct_reply(response_txt)

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

        good_reactions = [
            "mona", "sasuga", "azs", "ok_hand", "ii_hanashi", "kf-sugoi", "kami", "tada", "+1", "arigatou"
        ]

        if message.body["reaction"] in good_reactions:

            try:
                # いいね！チップを送金する
                from_user_wallet = Wallet(from_user.address, from_user.privkey)
                from_user_wallet.sendto(to_user.address, Symbol.ITB, Decimal("100"))

                # いいね！報酬を付与する
                faunder_wallet = Wallet(ITB_FOUNDATION_ADDRESS, ITB_FOUNDATION_PRIVKEY)
                faunder_wallet.sendto(from_user.address, Symbol.ITB, Decimal("1000"))
                faunder_wallet.sendto(to_user.address, Symbol.ITB, Decimal("1000"))

                response_txt = "いいね！のご利用ありがとうございました。"

            except Exception as ex:
                response_txt = str(ex)

            message.direct_reply(response_txt)

    # DBセッションを閉じる
    db_context.session.close()

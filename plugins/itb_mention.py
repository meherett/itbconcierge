import random
import re
from decimal import Decimal

from slackbot.bot import default_reply, listen_to, react_to, respond_to
from slackbot.dispatcher import Message
from sqlalchemy.sql.functions import func

from slackbot_settings import (CONTRACT_ADDRESS, GOOD_REACTIONS,
                               ITB_FOUNDATION_ADDRESS)

from .model import DBContext, ShopItem, ShopOrder, Symbol, User
from .wallet import WalletController
from .withdrawal import WithdrawalController

# いいね！を欲した者
greedies = []


@listen_to("ITB.*ヘルプ", re.IGNORECASE)
@respond_to("ITB.*ヘルプ", re.IGNORECASE)
def itb_get_help(message: Message):

    response_txt = "```\n"
    response_txt += "ITBトークンとは\n"
    response_txt += "    ITBトークンとは、IT分科会を主体とし、発行されたトークンのことです。\n"
    response_txt += "    社内の良好なコミュニケーションの実現を目的とし、\n"
    response_txt += "    これを実現するため、各種サービスの提供を計画しています。\n"
    response_txt += "    初期リリース時に提供されるサービスとして、「いいね！チップ送信機能」があります。\n"
    response_txt += "    Slackで「いいね！」をすると、ITBトークンがチップとして送付されます。\n"
    response_txt += "    さぁ、ITBコンシェルジュサービスに入会し、ITBトークンを送りあいましょう。\n"
    response_txt += "\n"
    response_txt += "ITBコンシェルジュサービスとは\n"
    response_txt += "    良いサービスとは誰でも気軽に利用できるサービスであると考えています。\n"
    response_txt += "    そこでITBトークンを気軽に送りあえるプラットフォームをSlack上に構築しました。\n"
    response_txt += "    このプラットフォームの名前が「ITBコンシェルジュサービス」です。\n"
    response_txt += "    「ITBコンシェルジュ」が招待されているチェンネルであれば、\n"
    response_txt += "    どこでもサービスを受けることができます。\n"
    response_txt += "\n"
    response_txt += "ITBカフェとは\n"
    response_txt += "    みなさん、ビットコインで商品を購入した経験はございますか？\n"
    response_txt += "    ITBCafeでは、トークンエコノミーをより身近に感じていただくため、\n"
    response_txt += "    ITBトークンを使った購入体験を提供したいと考えております。\n"
    response_txt += "    現在は有志によって運営されおりますが、持続可能な運営体制を構築してまいります。\n"
    response_txt += "\n"
    response_txt += "グッドコミュニケーションボーナスとは\n"
    response_txt += "    一般的なブロックチェーンはProof Of Workと呼ばれるコンセンサスアルゴリズムを使用しています。\n"
    response_txt += "    一方、ITBトークンは、Proof Of Happinessを採用しています。\n"
    response_txt += "    皆さんの良好なコミュニケーションがトークンの源泉になります。(適当\n"
    response_txt += "\n"
    response_txt += "ITB ヘルプ\n"
    response_txt += "    ITBコンシェルジュサービスで利用できるコマンドと説明を表示します。\n"
    response_txt += "\n"
    response_txt += "ITB 入会\n"
    response_txt += "    ITBコンシェルジュサービスに入会します。\n"
    response_txt += "    入会するとETHアドレスが新規発行され、ITBトークンを利用できるようになります。\n"
    response_txt += "    新規発行されたETHアドレスと秘密鍵は、入会したユーザーにDMで通知します。\n"
    response_txt += "    サービスを提供するため、このアドレスの秘密鍵はコンシェルジュでもお預かりします。\n"
    response_txt += "\n"
    response_txt += "ITB 退会\n"
    response_txt += "    ITBコンシェルジュサービスを退会します。\n"
    response_txt += "\n"
    response_txt += "ITB 残高照会\n"
    response_txt += "    ITBトークンの残高を取得します。\n"
    response_txt += "\n"
    response_txt += "ITB 通知 (ON/OFF)\n"
    response_txt += "    ITBコンシェルジュからの通知を受け取りたくない場合、OFFに設定します。\n"
    response_txt += "\n"
    response_txt += "ITBCafe 商品一覧\n"
    response_txt += "    ITBCafeで購入できる商品一覧を取得します。\n"
    response_txt += "\n"
    response_txt += "ITBCafe 購入 {商品名}\n"
    response_txt += "    ITBCafeで商品を購入します。\n"
    response_txt += "\n"
    response_txt += "ITBCafe 商品登録 {商品名} {商品価格}\n"
    response_txt += "    ITBCafeで購入できる商品を登録します。\n"
    response_txt += "\n"
    response_txt += "ITBCafe 商品削除 {商品名}\n"
    response_txt += "    ITBCafeで購入できる商品を削除します。\n"
    response_txt += "```"

    message.reply(response_txt)


@respond_to("ITB.*入会", re.IGNORECASE)
@listen_to("ITB.*入会", re.IGNORECASE)
def itb_join_membership(message: Message):

    # DBセッションを開く
    db_context = DBContext()

    # ユーザーを取得する
    slack_uid = message.user["id"]
    user = User.get_user_from_slack_uid(db_context, slack_uid)

    # ユーザー登録されている場合
    if user is not None:

        response_txt = "既にITBコンシェルジュサービスに入会しています。"
        message.reply(response_txt)

        response_txt = "ITBコンシェルジュサービスへようこそ。\n"
        response_txt += "あなたのアカウント情報はこちらです。\n"
        response_txt += "この秘密鍵は外部ウォレットで利用することができます。\n"
        response_txt += "```\n"
        response_txt += "slack_uid:{}\n"
        response_txt += "eth_address:{}\n"
        response_txt += "eth_privkey:{}\n"
        response_txt += "https://ropsten.etherscan.io/token/{}?a={}\n"
        response_txt += "```"
        response_txt = response_txt.format(
            user.slack_uid, user.eth_address, user.eth_privkey, CONTRACT_ADDRESS, user.eth_address
        )
        message.direct_reply(response_txt)

    # ユーザー登録されていない場合
    else:

        # ユーザーを新規登録する
        user = User(
            slack_uid=slack_uid,
            slack_name=message.user["real_name"],
            notification_enabled=True,
            created_at=func.now(),
            updated_at=func.now()
        )
        db_context.session.add(user)
        db_context.session.flush()

        # 新規アドレスを発行する
        eth_address, eth_privkey = WalletController.create_address(user.id)
        user.eth_address = eth_address
        user.eth_privkey = eth_privkey

        response_txt = "ITBコンシェルジュサービスへ入会しました。"
        message.reply(response_txt)

        response_txt = "ITBコンシェルジュサービスへようこそ。\n"
        response_txt += "あなたのアカウント情報はこちらです。\n"
        response_txt += "この秘密鍵は外部ウォレットで利用することができます。\n"
        response_txt += "```\n"
        response_txt += "slack_uid:{}\n"
        response_txt += "eth_address:{}\n"
        response_txt += "eth_privkey:{}\n"
        response_txt += "https://ropsten.etherscan.io/token/{}?a={}\n"
        response_txt += "```"
        response_txt = response_txt.format(
            user.slack_uid, user.eth_address, user.eth_privkey, CONTRACT_ADDRESS, user.eth_address
        )
        message.direct_reply(response_txt)

        # ガス代を付与する
        wc = WithdrawalController(db_context)
        wc.request_to_withdraw(
            Symbol.ETH,
            Decimal("1"),
            ITB_FOUNDATION_ADDRESS,
            user.eth_address,
            "ガス代補充"
        )

        # 新規登録ボーナスを付与する
        wc.request_to_withdraw(
            Symbol.ITB,
            Decimal("1000"),
            ITB_FOUNDATION_ADDRESS,
            user.eth_address,
            "新規登録ボーナス"
        )

        # コミット
        db_context.session.commit()

    # DBセッションを閉じる
    db_context.session.close()


@respond_to("ITB.*退会", re.IGNORECASE)
@listen_to("ITB.*退会", re.IGNORECASE)
def itb_cancel_membership(message: Message):

    # DBセッションを開く
    db_context = DBContext()

    # ユーザーを取得する
    slack_uid = message.user["id"]
    user = User.get_user_from_slack_uid(db_context, slack_uid)

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

    # ユーザーを取得する
    slack_uid = message.user["id"]
    user = User.get_user_from_slack_uid(db_context, slack_uid)

    # ユーザー登録されていない場合
    if user is None:

        response_txt = "ITBコンシェルジュサービスを利用するには入会する必要があります。"
        message.reply(response_txt)

    # ユーザー登録されている場合
    else:

        user_wallet = WalletController(user.eth_address, user.eth_privkey)
        itb_balance = user_wallet.get_balance(Symbol.ITB)

        response_txt = "ITBトークンの残高は「{} ITB」です。"
        response_txt = response_txt.format(
            itb_balance
        )
        message.reply(response_txt)

    # DBセッションを閉じる
    db_context.session.close()


@listen_to("ITB.*通知", re.IGNORECASE)
@respond_to("ITB.*通知", re.IGNORECASE)
def itb_switch_notification_enabled(message: Message):

    # DBセッションを開く
    db_context = DBContext()

    # ユーザーを取得する
    slack_uid = message.user["id"]
    user = User.get_user_from_slack_uid(db_context, slack_uid)

    # ユーザー登録されていない場合
    if user is None:

        response_txt = "ITBコンシェルジュサービスを利用するには入会する必要があります。"
        message.reply(response_txt)

    # ユーザー登録されている場合
    else:

        # メッセージ本文を取得する
        message_body = message.body["text"]

        # メッセージを要素に分解する
        m = re.match("(^ITB.*通知.*?)(ON|OFF)(.*$)", message_body, re.IGNORECASE)

        if m:
            if m.group(2).upper() == "ON":
                user.notification_enabled = True
                response_txt = "通知をONにしました。"
                message.reply(response_txt)
            else:
                user.notification_enabled = False
                response_txt = "通知をONにしました。"
                message.reply(response_txt)

        # コミット
        db_context.session.commit()

    # DBセッションを閉じる
    db_context.session.close()


@react_to(".*", re.IGNORECASE)
def itb_do_reaction(message: Message):

    # DBセッションを開く
    db_context = DBContext()

    # 送金元ユーザーを取得する
    from_slack_uid = message.user["id"]
    from_user = User.get_user_from_slack_uid(db_context, from_slack_uid)

    # 送金先ユーザーを取得する
    to_slack_uid = message.body["item_user"]
    to_user = User.get_user_from_slack_uid(db_context, to_slack_uid)

    # いずれのユーザーも登録されている場合
    if from_user and to_user:

        if message.body["reaction"] in GOOD_REACTIONS:

            # いいね！チップを送金する
            wc = WithdrawalController(db_context)
            wc.request_to_withdraw(
                Symbol.ITB,
                Decimal("30"),
                from_user.eth_address,
                to_user.eth_address,
                "いいね！チップ"
            )

            # いいね！ボーナスを付与する
            wc.request_to_withdraw(
                Symbol.ITB,
                Decimal("50"),
                ITB_FOUNDATION_ADDRESS,
                from_user.eth_address,
                "グッドコミュニケーションボーナス"
            )
            wc.request_to_withdraw(
                Symbol.ITB,
                Decimal("50"),
                ITB_FOUNDATION_ADDRESS,
                to_user.eth_address,
                "グッドコミュニケーションボーナス"
            )

            # コミット
            db_context.session.commit()

    # DBセッションを閉じる
    db_context.session.close()


@listen_to("ITBCafe.*商品登録", re.IGNORECASE)
@respond_to("ITBCafe.*商品登録", re.IGNORECASE)
def itbcafe_create_shopitem(message: Message):

    # DBセッションを開く
    db_context = DBContext()

    # ユーザーを取得する
    slack_uid = message.user["id"]
    user = User.get_user_from_slack_uid(db_context, slack_uid)

    # ユーザー登録されていない場合
    if user is None:

        response_txt = "ITBコンシェルジュサービスを利用するには入会する必要があります。"
        message.reply(response_txt)

    # ユーザー登録されている場合
    else:

        # メッセージ本文を取得する
        message_body = message.body["text"]

        # メッセージを要素に分解する
        m = re.match("(^ITB.*商品登録)\s(.*?)\s(.*?)($)", message_body, re.IGNORECASE)

        if m:

            validation_errors = []

            # 入力値を検証する(商品名)
            name = str(m.group(2)).replace(" ", "").replace("　", "")
            if len(name) == 0:
                validation_errors.append("商品名を入力してください。")

            # 入力値を検証する(商品価格)
            try:
                price = Decimal(int(m.group(3)))
                if price < Decimal('1'):
                    validation_errors.append("商品価格は1 ITB以上の整数で入力してください。")
            except:
                validation_errors.append("商品価格は1 ITB以上の整数で入力してください。")

            if len(validation_errors) == 0:

                item = db_context.session.query(ShopItem) \
                    .filter(ShopItem.name == name) \
                    .first()

                # 商品が登録されている場合、登録を更新する
                if item:
                    item.price = price
                    item.available = True
                    item.updated_at = func.now()

                # 商品が登録されていない場合、新規登録する
                else:
                    item = ShopItem(
                        name=name,
                        price=price,
                        available=True,
                        created_at=func.now(),
                        updated_at=func.now()
                    )
                    db_context.session.add(item)
                    db_context.session.flush()

                # コミット
                db_context.session.commit()

                response_txt = "商品「{} ({:.0f} ITB)」を登録しました。"
                response_txt = response_txt.format(
                    item.name, item.price
                )
                message.reply(response_txt)

            else:
                response_txt = "\n".join(validation_errors)
                message.reply(response_txt)
        else:
            response_txt = "商品登録は下記のフォーマットで入力してください。\n"
            response_txt += "「ITB 商品登録 {商品名} {商品価格}」"
            message.reply(response_txt)

    # DBセッションを閉じる
    db_context.session.close()


@listen_to("ITBCafe.*商品削除", re.IGNORECASE)
@respond_to("ITBCafe.*商品削除", re.IGNORECASE)
def itbcafe_delete_shopitem(message: Message):

    # DBセッションを開く
    db_context = DBContext()

    # ユーザーを取得する
    slack_uid = message.user["id"]
    user = User.get_user_from_slack_uid(db_context, slack_uid)

    # ユーザー登録されていない場合
    if user is None:

        response_txt = "ITBコンシェルジュサービスを利用するには入会する必要があります。"
        message.reply(response_txt)

    # ユーザー登録されている場合
    else:

        # メッセージ本文を取得する
        message_body = message.body["text"]

        # メッセージを要素に分解する
        m = re.match("(^ITB.*商品削除)\s(.*?)($)", message_body, re.IGNORECASE)

        if m:

            validation_errors = []

            # 入力値を検証する(商品名)
            name = str(m.group(2)).replace(" ", "").replace("　", "")
            if len(name) == 0:
                validation_errors.append("商品名を入力してください。")

            if len(validation_errors) == 0:

                item = db_context.session.query(ShopItem) \
                    .filter(ShopItem.name == name) \
                    .first()

                # 商品が登録されている場合、登録を削除する(論理削除)
                if item:
                    item.available = False
                    item.updated_at = func.now()

                    # コミット
                    db_context.session.commit()

                    response_txt = "商品「{}」を削除しました。"
                    response_txt = response_txt.format(
                        item.name
                    )
                    message.reply(response_txt)

                # 商品が登録されていない場合
                else:
                    response_txt = "商品「{}」は登録されていません。"
                    response_txt = response_txt.format(
                        name
                    )
                    message.reply(response_txt)

            else:
                response_txt = "\n".join(validation_errors)
                message.reply(response_txt)
        else:
            response_txt = "商品削除は下記のフォーマットで入力してください。\n"
            response_txt += "「ITB 商品削除 {商品名}」"
            message.reply(response_txt)

    # DBセッションを閉じる
    db_context.session.close()


@listen_to("ITBCafe.*商品一覧", re.IGNORECASE)
@respond_to("ITBCafe.*商品一覧", re.IGNORECASE)
def itbcafe_list_shopitem(message: Message):

    # DBセッションを開く
    db_context = DBContext()

    # ユーザーを取得する
    slack_uid = message.user["id"]
    user = User.get_user_from_slack_uid(db_context, slack_uid)

    # ユーザー登録されていない場合
    if user is None:

        response_txt = "ITBコンシェルジュサービスを利用するには入会する必要があります。"
        message.reply(response_txt)

    # ユーザー登録されている場合
    else:

        items = db_context.session.query(ShopItem) \
            .filter(ShopItem.available == True) \
            .all()

        if len(items) > 0:

            response_txt = "現在、下記の商品を購入できます。\n"
            response_txt += "```\n"
            for item in items:
                response_txt += "・{} ({:.0f} ITB)\n".format(item.name, item.price)
            response_txt += "```"
            message.reply(response_txt)

        else:

            response_txt = "現在、購入できる商品はありません。\n"
            message.reply(response_txt)

    # DBセッションを閉じる
    db_context.session.close()


@listen_to("ITBCafe.*購入", re.IGNORECASE)
@respond_to("ITBCafe.*購入", re.IGNORECASE)
def itbcafe_buy_shopitem(message: Message):

    # DBセッションを開く
    db_context = DBContext()

    # ユーザーを取得する
    slack_uid = message.user["id"]
    user = User.get_user_from_slack_uid(db_context, slack_uid)

    # ユーザー登録されていない場合
    if user is None:

        response_txt = "ITBコンシェルジュサービスを利用するには入会する必要があります。"
        message.reply(response_txt)

    # ユーザー登録されている場合
    else:

        # メッセージ本文を取得する
        message_body = message.body["text"]

        # メッセージを要素に分解する
        m = re.match("(^ITB.*購入)\s(.*?)($)", message_body, re.IGNORECASE)

        if m:

            validation_errors = []

            # 入力値を検証する(商品名)
            name = str(m.group(2)).replace(" ", "").replace("　", "")
            if len(name) == 0:
                validation_errors.append("商品名を入力してください。")

            if len(validation_errors) == 0:

                item = db_context.session.query(ShopItem) \
                    .filter(ShopItem.name == name) \
                    .filter(ShopItem.available == True) \
                    .first()

                # 商品が登録されている場合
                if item:

                    # 商品を購入する
                    user_wallet = WalletController(user.eth_address, user.eth_privkey)
                    is_success, tx_hash, error_reason = user_wallet.send_to(ITB_FOUNDATION_ADDRESS, Symbol.ITB, Decimal(item.price))

                    # 結果を通知する
                    if is_success == True:

                        order = ShopOrder(
                            userid=user.id,
                            name=item.name,
                            price=item.price,
                            ordered_at=func.now(),
                            created_at=func.now(),
                            updated_at=func.now()
                        )
                        db_context.session.add(order)
                        db_context.session.commit()

                        response_txt = "{}の購入が完了しました:yum: (-{:.0f} ITB)\n"
                        response_txt += "https://ropsten.etherscan.io/tx/{}"
                        response_txt = response_txt.format(
                            item.name, item.price, tx_hash
                        )
                        message.reply(response_txt)
                    else:
                        response_txt = "{}の購入に失敗しました:sob:\n"
                        response_txt += "{}"
                        response_txt = response_txt.format(
                            item.name, error_reason
                        )
                        message.reply(response_txt)

                    # いいね！を欲した者に登録する
                    if is_success and item["name"].find("いいね") > -1:
                        add_to_greedies(message.user["id"])

                # 商品が登録されていない場合
                else:
                    response_txt = "取り扱いのない商品です。"
                    message.reply(response_txt)
            else:
                response_txt = "\n".join(validation_errors)
                message.reply(response_txt)
        else:
            response_txt = "購入は下記のフォーマットで入力してください。\n"
            response_txt += "「ITB 購入 {商品名}」"
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

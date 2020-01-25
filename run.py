from slackbot.bot import Bot
from plugins.withdrawal import WithdrawalExecutor


def main():

    we = WithdrawalExecutor()
    we.start()

    bot = Bot()
    bot.run()

    we.request_stop()
    we.join()


if __name__ == "__main__":
    print("start ITB Concierge.")
    main()

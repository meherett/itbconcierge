from slackbot.bot import Bot

from plugins.withdrawal import WithdrawalExecutor
from plugins.report import ReportPublisher


def main():

    we = WithdrawalExecutor()
    we.start()
    rp = ReportPublisher()
    rp.start()

    bot = Bot()
    bot.run()

    we.request_stop()
    we.join()
    rp.request_stop()
    rp.join()


if __name__ == "__main__":
    print("start ITB Concierge.")
    main()

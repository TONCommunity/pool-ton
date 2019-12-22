from pool_ton_bot import bot


def main():
    tg_bot = bot.Bot()
    tg_bot.add_handlers()
    # tg_bot.add_jobs()
    tg_bot.start()


if __name__ == '__main__':
    main()

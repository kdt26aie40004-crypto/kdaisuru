import sys


def main():
    # 通常はウィンドウ版、`--cli` 指定時はコンソール版で起動する
    if "--cli" in sys.argv[1:]:
        import cli
        cli.run()
    else:
        import gui
        gui.run()


if __name__ == "__main__":
    main()

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    if arguments.self_test:
        from pdf_to_excel.self_test import run_self_test

        return run_self_test(arguments.output)

    from pdf_to_excel.gui.main_window import run

    return run()


if __name__ == "__main__":
    raise SystemExit(main())

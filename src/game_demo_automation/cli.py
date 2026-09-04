import argparse

from .compiler import write_task_bundle
from .models import Demonstration


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile a synchronized game demonstration")
    commands = parser.add_subparsers(dest="command", required=True)
    compile_parser = commands.add_parser("compile")
    compile_parser.add_argument("demonstration")
    compile_parser.add_argument("output")
    args = parser.parse_args()
    demo = Demonstration.load(args.demonstration)
    output = write_task_bundle(demo, args.output)
    print(f"Task bundle written to {output.resolve()}")

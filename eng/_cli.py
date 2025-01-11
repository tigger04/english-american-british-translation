import sys
import typing
from argparse import ArgumentParser
from ._fixer import PythonFixer, Target, TextFixer, Fixer, LiteralFixer

# Modified this to process input from STDIN and write output to STDOUT only
# the previous version of this fork would overwrite the input file without warning,
# which is not great.

def main(argv: typing.List[str]) -> int:
    parser = ArgumentParser()
    parser.add_argument("--target", default="us", choices=("us", "uk"))
    parser.add_argument(
        "--mode",
        default="text",
        choices=("text", "python", "literal"),
        help="Processing mode for the input",
    )
    args = parser.parse_args(argv)

    # Read from STDIN
    content = sys.stdin.read()

    # Select the appropriate fixer
    fixer_class: typing.Type[Fixer]
    if args.mode == "python":
        fixer_class = PythonFixer
    elif args.mode == "literal":
        fixer_class = LiteralFixer
    else:
        fixer_class = TextFixer

    # Process the content
    fixer = fixer_class(
        content=content,
        target=Target(args.target),
    )
    new_content = fixer.apply()

    # Write to STDOUT
    sys.stdout.write(new_content)
    return 0


def entrypoint():
    sys.exit(main(sys.argv[1:]))

import enum
import re
import sys
import tokenize
import typing
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType

from ._replacement import Replacement



REX_STRING = re.compile(r'\"[^"\\]*(?:\\.[^"\\]*)*"')


class Target(enum.Enum):
    US = "us"
    UK = "uk"


# @lru_cache(maxsize=2)
# def get_words(target: Target) -> typing.Mapping[str, str]:
#     path = Path(__file__).parent / 'words.txt'
#     result = {}
#     for line in path.open('r', encoding='utf8'):
#         line = line.strip()
#         if not line:
#             continue
#         uk, us = line.split('\t')
#         if target == Target.US:
#             result[uk] = us
#         else:
#             result[us] = uk
#     return MappingProxyType(result)


_UK_TO_US_WORDS: typing.Optional[typing.Mapping[str, str]] = None
_US_TO_UK_WORDS: typing.Optional[typing.Mapping[str, str]] = None

def _load_words_file(filename: str) -> typing.Mapping[str, str]:
    result = {}
    # Go up one level from the module directory to find dictionaries/
    path = Path(__file__).parent.parent / "dictionaries" / filename
    for line in path.open("r", encoding="utf8"):
        line = line.strip()
        if not line:
            continue
        try:
            word_from, word_to = line.split("\t")
            result[word_from] = word_to
        except ValueError:
            continue
    return MappingProxyType(result)

def get_words(target: Target) -> typing.Mapping[str, str]:
    global _UK_TO_US_WORDS, _US_TO_UK_WORDS
    
    if target == Target.US:
        if _UK_TO_US_WORDS is None:
            _UK_TO_US_WORDS = _load_words_file("words-uk-to-us.txt")
        return _UK_TO_US_WORDS
    else:
        if _US_TO_UK_WORDS is None:
            _US_TO_UK_WORDS = _load_words_file("words-us-to-uk.txt")
        return _US_TO_UK_WORDS


class Fixer:
    def __init__(
        self,
        content: str,
        target: Target,
        verbose: bool = False
    ) -> None:
        self.content = content
        self.target = target
        self.verbose = verbose

    @property
    def words(self) -> typing.Mapping[str, str]:
        return get_words(target=self.target)

    def apply(self) -> str:
        result = self.content
        # Sort replacements by length (longest first) to handle overlapping terms
        reps = sorted(self.replacements, reverse=True)
        for rep in reps:
            if rep.word_from in result:
                if self.verbose:
                    sys.stderr.write(f"Replacing '{rep.word_from}' with '{rep.word_to}'\n")
                result = rep.apply(result)
        return result


class PythonFixer(Fixer):
    @property
    def tokens(self) -> typing.Tuple[tokenize.TokenInfo, ...]:
        lines = self.content.split("\n")
        callback = (line + "\n" for line in lines).__next__
        return tuple(tokenize.generate_tokens(callback))

    @property
    def replacements(self) -> typing.Iterator[Replacement]:
        for token in self.tokens:
            if token.type not in {tokenize.STRING, tokenize.COMMENT}:
                continue
            yield from Replacement.from_token(token, self.words)


class TextFixer(Fixer):
    @property
    def replacements(self) -> typing.Iterator[Replacement]:
        token = tokenize.TokenInfo(
            type=tokenize.STRING,
            string=self.content,
            start=(1, 0),
            end=(2, 0),
            line=self.content,
        )
        yield from Replacement.from_token(token, self.words)


class LiteralFixer(Fixer):
    @property
    def replacements(self) -> typing.Iterator[Replacement]:
        for row_offset, line in enumerate(self.content.split("\n")):
            for match in REX_STRING.finditer(line):
                token = tokenize.TokenInfo(
                    type=tokenize.STRING,
                    string=match.group(0),
                    start=(1 + row_offset, match.start()),
                    end=(2 + row_offset, 0),
                    line=self.content,
                )
                yield from Replacement.from_token(token, self.words)

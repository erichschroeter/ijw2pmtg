import logging
import re
from abc import ABC, abstractmethod


class CardParserFactory(ABC):
    @abstractmethod
    def create_parser(self, file_path) -> object:
        pass


class Format1FormatFactory(CardParserFactory):
    def create_parser(self) -> object:
        return CardKingdomFormat1Parser()

class Format2FormatFactory(CardParserFactory):
    def create_parser(self) -> object:
        return CardKingdomFormat2Parser()

class Format3FormatFactory(CardParserFactory):
    def create_parser(self) -> object:
        return CardKingdomFormat3Parser()

class ManaBoxFormatFormatFactory(CardParserFactory):
    def create_parser(self) -> object:
        return ManaBoxFormatParser()


class CardParser(ABC):
    @abstractmethod
    def parse_line(self, line: str):
        pass

    def parse(self, file_path: str) -> list:
        with open(file_path, 'r') as file:
            cards = []
            for line in file:
                if not line or re.match(r'^(\/+|#)(.*)', line):
                    continue  # Empty line or comment
                if re.match(r'^\[.*\]', line):
                    continue  # Section header
                cards_in_line = self.parse_line(line.strip())
                if cards_in_line:
                    cards.append(cards_in_line)
            return cards


class CardKingdomFormat1Parser(CardParser):
    def parse_line(self, line: str):
        match = re.search(r'^\s*(?P<quantity>\d+)\s+(?P<card>.*)', line)
        return match.group('card')

class CardKingdomFormat2Parser(CardParser):
    def parse_line(self, line: str):
        match = re.search(r'^\s*(?P<quantity>\d+)x\s+(?P<card>.*)', line)
        return match.group('card')

class CardKingdomFormat3Parser(CardParser):
    def parse_line(self, line: str):
        return line.strip()

class ManaBoxFormatParser(CardParser):
    def parse_line(self, line: str):
        match = re.search(r'^\s*(?P<card>.+)\((?P<setname>.*)\)\s+(?P<printno>\d+)', line)
        return match.group('card')


def detect_format(file_path: str) -> CardParserFactory:
    # Read beginning of file to check file format
    with open(file_path, 'r') as file:
        # head = [next(file) for _ in range(1)]
        head = file.readline().strip()
        # Determine the text file format based on some logic or condition
        logging.warning(f'detecting: "{head}"')
        if re.match(r'^.+\(.*\)\s+\d*', head):
            return ManaBoxFormatFormatFactory()
        elif re.match(r'^\d+x', head):
            return Format2FormatFactory()
        elif re.match(r'^\d+', head):
            return Format1FormatFactory()
        # elif "," in head:  # Format 2
        #     return Format2FormatFactory()
        else:
            return Format3FormatFactory()

def parse_text_file(text: str) -> dict:
    factory = detect_text_file_format(text)
    parser = factory.create_parser()
    return parser.parse(text)

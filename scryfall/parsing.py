import csv
import logging
import os
import re
from abc import ABC, abstractmethod
from io import StringIO


class CardParser(ABC):
    @abstractmethod
    def parse_card(self, line: str):
        pass

    def parse_cards(self, file_path: str) -> list:
        with open(file_path, 'r') as file:
            cards = []
            skip_first_line = os.path.splitext(file_path)[1] == '.csv'
            for line in file:
                if skip_first_line:
                    skip_first_line = False
                    continue
                if not line or re.match(r'^(\/+|#)(.*)', line):
                    continue  # Empty line or comment
                if re.match(r'^\[.*\]', line):
                    continue  # Section header
                cards_in_line = self.parse_card(line.strip())
                if cards_in_line:
                    cards.append(cards_in_line)
            return cards


class CardKingdomFormat1Parser(CardParser):
    def parse_card(self, line: str):
        match = re.search(r'^\s*(?P<quantity>\d+)\s+(?P<card>.*)', line)
        return match.group('card')

class CardKingdomFormat2Parser(CardParser):
    def parse_card(self, line: str):
        match = re.search(r'^\s*(?P<quantity>\d+)x\s+(?P<card>.*)', line)
        return match.group('card')

class CardKingdomFormat3Parser(CardParser):
    def parse_card(self, line: str):
        return line.strip()

class ManaBoxExportFormatParser(CardParser):
    def parse_card(self, line: str):
        match = re.search(r'^(?P<quantity>\d*)\s*(?P<card>.+)\((?P<setname>.*)\)\s+(?P<printno>\d+)', line)
        if match and match.groupdict().get('card'):
            return match.group('card').strip()

class ManaBoxCollectionFormatParser(CardParser):
    def parse_card(self, line: str):
        csv_line = StringIO(line)
        reader = csv.reader(csv_line)
        for row in reader:
            # Assume first column is card Name
            return row[0]


class CardParserFactory(ABC):
    def create_parser(self, file_path: str) -> CardParser:
        # Read beginning of file to check file format
        if os.path.splitext(file_path)[1] == '.csv':
            return ManaBoxCollectionFormatFactory().create_parser(file_path)
        else:
            with open(file_path, 'r') as file:
                for line in file:
                    if not line or re.match(r'^(\/+|#)(.*)', line):
                        continue  # ignore empty lines and comments
                    # head = [next(file) for _ in range(1)]
                    # head = file.readline().strip()
                    head = line.strip()
                    # Determine the text file format based on some logic or condition
                    logging.warning(f'detecting: "{head}"')
                    if re.match(r'^.+\(.*\)\s+\d*', head):
                        return ManaBoxExportFormatFactory().create_parser(file_path)
                    elif re.match(r'^\d+x', head):
                        return Format2FormatFactory().create_parser(file_path)
                    elif re.match(r'^\d+', head):
                        return Format1FormatFactory().create_parser(file_path)
                    # elif "," in head:  # Format 2
                    #     return Format2FormatFactory().create_parser(file_path)
                    else:
                        return Format3FormatFactory().create_parser(file_path)


class Format1FormatFactory(CardParserFactory):
    def create_parser(self, file_path: str) -> CardParser:
        return CardKingdomFormat1Parser()

class Format2FormatFactory(CardParserFactory):
    def create_parser(self, file_path: str) -> CardParser:
        return CardKingdomFormat2Parser()

class Format3FormatFactory(CardParserFactory):
    def create_parser(self, file_path: str) -> CardParser:
        return CardKingdomFormat3Parser()

class ManaBoxExportFormatFactory(CardParserFactory):
    def create_parser(self, file_path: str) -> CardParser:
        return ManaBoxExportFormatParser()

class ManaBoxCollectionFormatFactory(CardParserFactory):
    def create_parser(self, file_path: str) -> CardParser:
        return ManaBoxCollectionFormatParser()

import argparse
import json
import logging
import os
import re
import sys
from .api import Scryfall

#region Command line parsing  # noqa


class ColorLogFormatter(logging.Formatter):
    '''
    Custom formatter that changes the color of logs based on the log level.
    '''

    grey = "\x1b[38;20m"
    green = "\u001b[32m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    blue = "\u001b[34m"
    cyan = "\u001b[36m"
    reset = "\x1b[0m"

    timestamp = '%(asctime)s - '
    loglevel = '%(levelname)s'
    message = ' - %(message)s'

    FORMATS = {
        logging.DEBUG:    timestamp + blue + loglevel + reset + message,
        logging.INFO:     timestamp + green + loglevel + reset + message,
        logging.WARNING:  timestamp + yellow + loglevel + reset + message,
        logging.ERROR:    timestamp + red + loglevel + reset + message,
        logging.CRITICAL: timestamp + bold_red + loglevel + reset + message
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def _init_logger(level=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(level)

    formatter = ColorLogFormatter()
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class RawTextArgumentDefaultsHelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter):
    pass


#endregion Command line parsing  # noqa

class App:
    def __init__(self) -> None:
        self.args = None
        self.parser = argparse.ArgumentParser(prog='scryfall')
        self.parser.add_argument('-v', '--verbosity',
                                 choices=['critical', 'error', 'warning', 'info', 'debug'],
                                 default='info',
                                 help='Set the logging verbosity level.')
        self.parser.add_argument('--server', default='https://api.scryfall.com', help="The Scryfall server URL.")
        self.parser.add_argument('--dryrun', default=False, help='Dry run network and filesystem operations.', action='store_true')
        self.parser.add_argument('-i', '--input',
                                 help='A file of card names. Alternatively, a newline-separated list of card names can be provided via stdin.')
        self.parser.add_argument('-o', '--output', default=os.getcwd(), help='The output directory.')
        self.parser.set_defaults(func=download_cards)

    def parse_args(self, args=None):
        self.args = self.parser.parse_args(args)

    def run(self):
        if not self.args:
            self.parse_args()
        _init_logger(getattr(logging, self.args.verbosity.upper()))
        logging.debug(f'command-line args: {self.args}')
        self.args.func(self.args)


class CardParser:
    def __init__(self, filename):
        self.cards = []
        with open(filename, 'r') as file:
            for line in file:
                cards_in_line = self.parse_line(line.strip())
                if cards_in_line:
                    # Filter out extra info that Manabox includes sometimes
                    if re.match(r'.+\(.*\)\s+\d*', cards_in_line[0]):
                        manabox = re.search(r'(?P<card>.+)\((?P<setname>.*)\)\s+(?P<printno>\d+)', cards_in_line[0])
                        self.cards.extend([manabox.group('card').strip()])
                    else:
                        self.cards.extend(cards_in_line)

    def parse_line(self, line):
        if not line or re.match(r'^(\/+|#)(.*)', line):
            # Empty line or comment
            return []
        elif re.match(r'\d+\s+(.*)', line):
            # Card Kingdom Format 1
            logging.debug(f'Matched Card Kingdom Format 1: "{line}"')
            match = re.search(r'(?P<quantity>\d+)\s+(?P<card>.*)', line)
            return [match.group('card')]
        elif re.match(r'\d+x\s+(.*)', line):
            # Card Kingdom Format 2
            logging.debug(f'Matched Card Kingdom Format 2: "{line}"')
            match = re.search(r'(?P<quantity>\d+)x\s+(?P<card>.*)', line)
            return [match.group('card')]
        elif line.strip():
            # Card Kingdom Format 3
            logging.debug(f'Matched Card Kingdom Format 3: "{line}"')
            return [line.strip()]
        else:
            return []

    def get_cards(self):
        return self.cards


def list_card_names(file_path=None):
    if file_path:
        logging.info(f'Reading card names from {file_path}')
        parser = CardParser(file_path)
        return parser.get_cards()
    else:
        logging.info(f'Reading card names from stdin')
        return [line.strip() for line in sys.stdin]


def download_cards(args):
    api = Scryfall(args.server)
    if args.dryrun:
        api.dryrun = True
    if not os.path.exists(args.output):
        os.makedirs(args.output, exist_ok=True)
    for card_name in list_card_names(args.input):
        response = api.cards_named(card_name)
        if response:
            response = response.json()
            logging.debug(f'{json.dumps(response)}')
            result = api.cards_image(response['id'])
            png = f'{args.output}/{card_name}.png'
            with open(png, 'wb') as f:
                logging.info(png)
                for chunk in result.iter_content(chunk_size=1024):
                    f.write(chunk)


def main():
    App().run()


if __name__ == '__main__':
    main()

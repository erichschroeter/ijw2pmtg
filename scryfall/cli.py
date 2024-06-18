from abc import ABC, abstractmethod
import argparse
import json
import logging
import os
import re
import sys
from .api import Scryfall
from .parsing import CardParserFactory

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


def dryrun(msg):
    green = "\u001b[32m"
    reset = "\x1b[0m"
    print(f'{green}DRYRUN{reset}: {msg}')


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
        self.parser.add_argument('cards', nargs='*', help='Names of Magic the Gathering (MTG) cards.')
        self.parser.set_defaults(func=download_cards)

    def parse_args(self, args=None):
        self.args = self.parser.parse_args(args)

    def run(self):
        if not self.args:
            self.parse_args()
        _init_logger(getattr(logging, self.args.verbosity.upper()))
        logging.debug(f'command-line args: {self.args}')
        self.args.func(self.args)


def list_card_names(args):
    if args.cards:
        cards = args.cards
    elif args.input:
        factory = CardParserFactory()
        parser = factory.create_parser(args.input)
        logging.error(parser)
        cards = parser.parse_cards(args.input)
    else:
        cards = [line.strip() for line in sys.stdin]
    logging.info(f'Found {len(cards)} cards.')
    return cards


def slugify(card_name):
    card_name = re.sub(r'[/\\<>|"\*\?:]', '_', card_name)
    return card_name


def download_cards(args):
    api = Scryfall(args.server)
    if not os.path.exists(args.output):
        os.makedirs(args.output, exist_ok=True)
    path_prefix = f'{args.output}/' if args.output else ''
    for card_name in list_card_names(args):
        if args.dryrun:
            dryrun(f'Downloading {card_name}')
            continue
        response = api.cards_named(card_name)
        if response:
            response = response.json()
            logging.debug(f'{json.dumps(response)}')
            result = api.cards_image(response['id'])
            png = f'{path_prefix}{slugify(card_name)}.png'
            with open(png, 'wb') as f:
                logging.info(png)
                for chunk in result.iter_content(chunk_size=1024):
                    f.write(chunk)


def main():
    App().run()


if __name__ == '__main__':
    main()

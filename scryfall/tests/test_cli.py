import io
import unittest
from unittest.mock import patch, MagicMock
import tempfile
from scryfall.api import Scryfall
from scryfall.cli import download_cards, list_card_names, Card, parse_card_input
import shutil
import os
import json


class TestParseCardInput(unittest.TestCase):
    def test_card_name(self):
        self.assertEqual(parse_card_input("Card Name"), Card(name="Card Name"))

    def test_card_name_with_comma(self):
        self.assertEqual(
            parse_card_input("Card Name, With Comma"),
            Card(name="Card Name, With Comma"),
        )

    def test_card_name_with_block_and_set_name(self):
        self.assertEqual(
            parse_card_input("Card Name (set code) Set Name"),
            Card(name="Card Name", block="set code", set_name="Set Name"),
        )

    def test_card_name_with_block(self):
        self.assertEqual(
            parse_card_input("Card Name (set code)"),
            Card(name="Card Name", block="set code"),
        )

    def test_card_name_with_comma_and_block_and_set_name(self):
        self.assertEqual(
            parse_card_input("Card Name, With Comma (set code) Set Name"),
            Card(name="Card Name, With Comma", block="set code", set_name="Set Name"),
        )

    def test_xquantity_card_name_with_block(self):
        self.assertEqual(
            parse_card_input("1x Card Name (set code)"),
            Card(quantity=1, name="Card Name", block="set code"),
        )

    def test_xquantity_card_name_with_block_and_set_name(self):
        self.assertEqual(
            parse_card_input("10x Card Name (set code) Set Name"),
            Card(quantity=10, name="Card Name", block="set code", set_name="Set Name"),
        )

    def test_xquantity_card_name(self):
        self.assertEqual(
            parse_card_input("5x Card Name"), Card(quantity=5, name="Card Name")
        )

    def test_quantity_card_name_with_block(self):
        self.assertEqual(
            parse_card_input("1 Card Name (set code)"),
            Card(quantity=1, name="Card Name", block="set code"),
        )

    def test_quantity_card_name_with_block_and_set_name(self):
        self.assertEqual(
            parse_card_input("10 Card Name (set code) Set Name"),
            Card(quantity=10, name="Card Name", block="set code", set_name="Set Name"),
        )

    def test_quantity_card_name(self):
        self.assertEqual(
            parse_card_input("5 Card Name"), Card(quantity=5, name="Card Name")
        )

    def test_comment_pound(self):
        self.assertEqual(parse_card_input("#5 Card Name"), None)

    def test_comment_double_slash(self):
        self.assertEqual(parse_card_input("// 5 Card Name"), None)


class TestListCardNames(unittest.TestCase):
    @patch("scryfall.api.Scryfall")
    def test_list_card_names_with_cards(self, MockScryfall):
        args = MagicMock()
        args.cards = ["Black Lotus"]
        args.input = None
        mock_api = MockScryfall.return_value
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "123",
            "name": "Black Lotus",
            "set_name": "Alpha",
            "collector_number": "1",
            "set": "LEA",
            "card_faces": [],
        }
        mock_api.cards_named.return_value = mock_response

        cards = list_card_names(args, mock_api)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].name, "Black Lotus")

    @patch("scryfall.api.Scryfall")
    @patch("scryfall.parsing.CardParserFactory")
    def test_list_card_names_with_input_file(self, MockScryfall, MockFactory):
        args = MagicMock()
        args.cards = None
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
            temp_file.write("Black Lotus\n")
            temp_file.flush()
            args.input = temp_file.name

            mock_api = MockScryfall.return_value
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "id": "123",
                "name": "Black Lotus",
                "set_name": "Alpha",
                "collector_number": "1",
                "set": "LEA",
                "card_faces": [],
            }
            mock_api.cards_named.return_value = mock_response

            mock_parser = MockFactory.return_value.create_parser.return_value
            mock_parser.parse_cards.return_value = ["Black Lotus"]
            cards = list_card_names(args, mock_api)
            self.assertEqual(len(cards), 1)
            self.assertEqual(cards[0].name, "Black Lotus")

    @patch("scryfall.api.Scryfall")
    @patch("sys.stdin", new_callable=io.StringIO)
    def test_list_card_names_with_stdin(self, mock_stdin, MockScryfall):
        args = MagicMock()
        args.cards = None
        args.input = None
        mock_api = MockScryfall.return_value
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "123",
            "name": "Black Lotus",
            "set_name": "Alpha",
            "collector_number": "1",
            "set": "LEA",
            "card_faces": [],
        }
        mock_api.cards_named.return_value = mock_response
        mock_stdin.write("Black Lotus\n")
        mock_stdin.seek(0)

        cards = list_card_names(args, mock_api)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].name, "Black Lotus")

    @patch("scryfall.api.Scryfall")
    def test_list_card_names_with_set(self, MockScryfall):
        args = MagicMock()
        args.cards = ["Black Lotus (LEA)"]
        args.input = None
        mock_api = MockScryfall.return_value
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "123",
            "name": "Black Lotus",
            "set_name": "Limited Edition Alpha",
            "collector_number": "1",
            "set": "LEA",
            "card_faces": [],
        }
        mock_api.cards_named.return_value = mock_response
        cards = list_card_names(args, mock_api)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].name, "Black Lotus")
        self.assertEqual(cards[0].block, "LEA")


if __name__ == "__main__":
    unittest.main()

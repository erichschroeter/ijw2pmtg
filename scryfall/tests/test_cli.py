import unittest
from unittest.mock import patch, mock_open
from io import StringIO
from scryfall.cli import list_card_names, CardParserFactory


class TestListCardNames(unittest.TestCase):

    def test_list_card_names_with_cards(self):
        args = type("", (), {})()  # Create a simple object to mock args
        args.cards = ["Black Lotus", "Mox Sapphire"]
        args.input = None
        with patch("scryfall.cli.logging.info") as mock_logging_info:
            result = list_card_names(args)
            self.assertEqual(result, ["Black Lotus", "Mox Sapphire"])
            mock_logging_info.assert_called_with("Found 2 cards.")

    @patch(
        "builtins.open", new_callable=mock_open, read_data="Black Lotus\nMox Sapphire\n"
    )
    def test_list_card_names_with_input_file(self, mock_file):
        args = type("", (), {})()  # Create a simple object to mock args
        args.cards = None
        args.input = "fake_file.txt"
        with patch("scryfall.cli.CardParserFactory") as MockCardParserFactory:
            mock_parser = MockCardParserFactory.return_value.create_parser.return_value
            mock_parser.parse_cards.return_value = ["Black Lotus", "Mox Sapphire"]
            with patch("scryfall.cli.logging.info") as mock_logging_info:
                result = list_card_names(args)
                self.assertEqual(result, ["Black Lotus", "Mox Sapphire"])
                mock_logging_info.assert_called_with("Found 2 cards.")

    @patch("sys.stdin", new_callable=StringIO)
    def test_list_card_names_with_stdin(self, mock_stdin):
        mock_stdin.write("Black Lotus\nMox Sapphire\n")
        mock_stdin.seek(0)
        args = type("", (), {})()  # Create a simple object to mock args
        args.cards = None
        args.input = None
        with patch("scryfall.cli.logging.info") as mock_logging_info:
            result = list_card_names(args)
            self.assertEqual(result, ["Black Lotus", "Mox Sapphire"])
            mock_logging_info.assert_called_with("Found 2 cards.")


if __name__ == "__main__":
    unittest.main()

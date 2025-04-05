import unittest
from unittest.mock import call, patch, MagicMock
from scryfall.api import Scryfall, Card, sanitize_card_name, unsanitize_card_name
import tempfile
import shutil
import os.path
import json
import pathlib


class TestSanitize(unittest.TestCase):
    def test_sanitize_card_name(self):
        test_cases = [
            ("Black Lotus", "Black Lotus"),
            ("Fire/Ice", "Fire__SLASH__Ice"),
            ("Question? Answer!", "Question__QUEST__ Answer!"),
            ("Card: With Symbols!", "Card__COLON__ With Symbols!"),
            ("File<>Name", "File__LT____GT__Name"),
            ("Path/To\\File", "Path__SLASH__To__BSLASH__File"),
            ('File "Name"', "File __QUOTE__Name__QUOTE__"),
            ("Wild * Card?", "Wild __STAR__ Card__QUEST__"),
            ("Path|Separator", "Path__PIPE__Separator"),
            ("Card_With_Underscores", "Card_With_Underscores"),
        ]
        for input_name, expected in test_cases:
            self.assertEqual(sanitize_card_name(input_name), expected)

    def test_unsanitize_card_name(self):
        test_cases = [
            ("Black Lotus", "Black Lotus"),
            ("Fire__SLASH__Ice", "Fire/Ice"),
            ("Question__QUEST__ Answer!", "Question? Answer!"),
            ("Card__COLON__ With Symbols!", "Card: With Symbols!"),
            ("File__LT____GT__Name", "File<>Name"),
            ("Path__SLASH__To__BSLASH__File", "Path/To\\File"),
            ("File __QUOTE__Name__QUOTE__", 'File "Name"'),
            ("Wild __STAR__ Card__QUEST__", "Wild * Card?"),
            ("Path__PIPE__Separator", "Path|Separator"),
            ("Card_With_Underscores", "Card_With_Underscores"),
        ]
        for input_name, expected in test_cases:
            self.assertEqual(unsanitize_card_name(input_name), expected)


class TestCardsNamed(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.scryfall = Scryfall(cache_dir=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("requests.get")
    def test_api_call(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "Black Lotus",
            "id": "b0faa7f2-b547-42c4-a810-839da50dadfe",
            "set": "lea",
            "set_name": "Limited Edition Alpha",
            "collector_number": "123",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # First call - should hit API
        response = self.scryfall.cards_named("Black Lotus")
        self.assertIsInstance(response, Card)
        self.assertEqual("Black Lotus", response.name)
        self.assertEqual("b0faa7f2-b547-42c4-a810-839da50dadfe", response.uuid)
        self.assertEqual("lea", response.block)
        expected_file = os.path.join(self.temp_dir.name, "data", "Black Lotus.LEA.json")
        self.assertTrue(
            os.path.exists(expected_file), f"Expected file not found: {expected_file}"
        )

        # Verify API was called
        mock_get.assert_called_with(
            "https://api.scryfall.com/cards/named?fuzzy=Black+Lotus"
        )

    @patch("requests.get")
    def test_api_call_with_set(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "Black Lotus",
            "id": "b0faa7f2-b547-42c4-a810-839da50dadfe",
            "set": "lea",
            "set_name": "Limited Edition Alpha",
            "collector_number": "123",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # First call - should hit API
        response = self.scryfall.cards_named("Black Lotus", set="LEA")
        self.assertIsInstance(response, Card)
        self.assertEqual("Black Lotus", response.name)
        self.assertEqual("b0faa7f2-b547-42c4-a810-839da50dadfe", response.uuid)
        self.assertEqual("lea", response.block)
        expected_file = os.path.join(self.temp_dir.name, "data", "Black Lotus.LEA.json")
        self.assertTrue(
            os.path.exists(expected_file), f"Expected file not found: {expected_file}"
        )

        # Verify API was called
        mock_get.assert_called_with(
            "https://api.scryfall.com/cards/named?fuzzy=Black+Lotus&set=LEA"
        )

    @patch("requests.get")
    def test_api_call_with_doublefaced(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "Bala Ged Recovery // Bala Ged Sanctuary",
            "id": "test-uuid",
            "set": "znr",
            "set_name": "Zendikar Rising",
            "collector_number": "180",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # First call - should hit API
        response = self.scryfall.cards_named(
            "Bala Ged Recovery // Bala Ged Sanctuary", set="ZNR"
        )
        self.assertIsInstance(response, Card)
        self.assertEqual("Bala Ged Recovery // Bala Ged Sanctuary", response.name)
        self.assertEqual("test-uuid", response.uuid)
        self.assertEqual("znr", response.block)
        expected_file = os.path.join(
            self.temp_dir.name,
            "data",
            "Bala Ged Recovery __SLASH____SLASH__ Bala Ged Sanctuary.ZNR.json",
        )
        self.assertTrue(
            os.path.exists(expected_file),
            f"Expected file not found: {expected_file}",
        )

        # Verify API was called
        mock_get.assert_called_with(
            "https://api.scryfall.com/cards/named?fuzzy=Bala+Ged+Recovery+%2F%2F+Bala+Ged+Sanctuary&set=ZNR"
        )


class TestCardsNamedCached(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.scryfall = Scryfall(cache_dir=self.temp_dir.name)
        # Copy local cache files for testing
        os.makedirs(
            os.path.join(os.path.dirname(__file__), "cache", "data"), exist_ok=True
        )
        shutil.copyfile(
            os.path.join(
                os.path.dirname(__file__),
                "cache",
                "data",
                "Black Lotus.LEA.json",
            ),
            os.path.join(self.temp_dir.name, "data", "Black Lotus.LEA.json"),
        )
        shutil.copyfile(
            os.path.join(
                os.path.dirname(__file__),
                "cache",
                "data",
                "Bala Ged Recovery __SLASH____SLASH__ Bala Ged Sanctuary.ZNR.json",
            ),
            os.path.join(
                self.temp_dir.name,
                "data",
                "Bala Ged Recovery __SLASH____SLASH__ Bala Ged Sanctuary.ZNR.json",
            ),
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("requests.get")
    def test_api_not_called(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "Black Lotus",
            "id": "b0faa7f2-b547-42c4-a810-839da50dadfe",
            "set": "lea",
            "set_name": "Limited Edition Alpha",
            "collector_number": "123",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # First call - should hit cache
        response = self.scryfall.cards_named("Black Lotus", set="LEA")
        self.assertIsInstance(response, Card)
        self.assertEqual("Black Lotus", response.name)
        self.assertEqual("b0faa7f2-b547-42c4-a810-839da50dadfe", response.uuid)
        self.assertEqual("lea", response.block)
        expected_file = os.path.join(self.temp_dir.name, "data", "Black Lotus.LEA.json")
        self.assertTrue(
            os.path.exists(expected_file), f"Expected file not found: {expected_file}"
        )

        # Verify API was not called
        mock_get.assert_not_called()

    @patch("requests.get")
    def test_api_not_called_with_doublefaced(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "name": "Bala Ged Recovery // Bala Ged Sanctuary",
            "id": "c5cb3052-358d-44a7-8cfd-cd31b236494a",
            "set": "znr",
            "set_name": "Zendikar Rising",
            "collector_number": "180",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # First call - should hit cache
        response = self.scryfall.cards_named(
            "Bala Ged Recovery // Bala Ged Sanctuary", set="ZNR"
        )
        self.assertIsInstance(response, Card)
        self.assertEqual("Bala Ged Recovery // Bala Ged Sanctuary", response.name)
        self.assertEqual("c5cb3052-358d-44a7-8cfd-cd31b236494a", response.uuid)
        self.assertEqual("znr", response.block)
        expected_file = os.path.join(
            self.temp_dir.name,
            "data",
            "Bala Ged Recovery __SLASH____SLASH__ Bala Ged Sanctuary.ZNR.json",
        )
        self.assertTrue(
            os.path.exists(expected_file),
            f"Expected file not found: {expected_file}",
        )

        # Verify API was not called
        mock_get.assert_not_called()


class TestScryfallCardsImage(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.scryfall = Scryfall(cache_dir=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("requests.get")
    def test_cards_image(self, mock_get):
        mock_response = MagicMock()
        mock_response.content = b"fake_image_data"
        mock_response.iter_content.return_value = [b"fake_image_data"]
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"content-type": "image/png"}
        mock_get.return_value = mock_response

        card = Card(name="Black Lotus", uuid="test-uuid")

        # First call - should hit API
        self.scryfall.cards_image(card)
        self.assertTrue(
            os.path.exists(
                os.path.join(self.temp_dir.name, "images", "Black Lotus.png")
            ),
            f"Expected file not found: {os.path.join(self.temp_dir.name, 'images', 'Black Lotus.png')}",
        )

        # Verify API was called
        mock_get.assert_called_with(
            "https://api.scryfall.com/cards/test-uuid?format=image&version=png"
        )

        # Second call - should hit cache
        response2 = self.scryfall.cards_image(card)
        self.assertEqual(response2, b"fake_image_data")

        # Verify API was only called once
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_cards_image_double_faced(self, mock_get):
        # Set up different responses for front and back faces
        front_response = MagicMock()
        front_response.content = b"front_face_image"
        front_response.iter_content.return_value = [b"front_face_image"]
        front_response.raise_for_status = MagicMock()
        front_response.headers = {"content-type": "image/png"}

        back_response = MagicMock()
        back_response.content = b"back_face_image"
        back_response.iter_content.return_value = [b"back_face_image"]
        back_response.raise_for_status = MagicMock()
        back_response.headers = {"content-type": "image/png"}

        # Configure mock to return different responses based on the URL
        def get_side_response(*args, **kwargs):
            if "face=back" in args[0]:
                return back_response
            return front_response

        mock_get.side_effect = get_side_response

        card = Card(name="Delver of Secrets", uuid="test-uuid", is_double_faced=True)

        # First call - should hit API and save front face
        response1 = self.scryfall.cards_image(card)
        self.assertEqual(response1, b"front_face_image")
        self.assertTrue(
            os.path.exists(
                os.path.join(self.temp_dir.name, "images", "Delver of Secrets.png")
            ),
            f"Expected file not found: {os.path.join(self.temp_dir.name, 'images', 'Delver of Secrets.png')}",
        )

        # Second call - should hit API and save back face
        response2 = self.scryfall.cards_image(card, face="back")
        self.assertEqual(response2, b"back_face_image")
        self.assertTrue(
            os.path.exists(
                os.path.join(self.temp_dir.name, "images", "Delver of Secrets.back.png")
            )
        )

        # Verify API was called with correct parameters for each face
        mock_get.assert_has_calls(
            [
                call(
                    "https://api.scryfall.com/cards/test-uuid?format=image&version=png"
                ),
                call(
                    "https://api.scryfall.com/cards/test-uuid?format=image&version=png&face=back"
                ),
            ]
        )

        # Third call to get front face - should hit cache
        response3 = self.scryfall.cards_image(card)
        self.assertEqual(response3, b"front_face_image")

        # Fourth call to get back face - should hit cache
        response4 = self.scryfall.cards_image(card, face="back")
        self.assertEqual(response4, b"back_face_image")

        # Verify no additional API calls were made
        self.assertEqual(mock_get.call_count, 2)


class TestScryfallCardsSearch(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.scryfall = Scryfall(cache_dir=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("requests.get")
    def test_cards_search(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": [
                {
                    "name": "Black Lotus",
                    "id": "test-uuid",
                    "set": "lea",
                    "set_name": "Limited Edition Alpha",
                    "collector_number": "123",
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = self.scryfall.cards_search("Black Lotus")
        self.assertIsInstance(response, list)
        self.assertEqual(len(response), 1)
        self.assertIsInstance(response[0], Card)
        self.assertEqual(response[0].name, "Black Lotus")
        self.assertEqual(response[0].uuid, "test-uuid")
        mock_get.assert_called_once()


class TestScryfall(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.scryfall = Scryfall(cache_dir=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cache_dirs_creation(self):
        cache_dir = pathlib.Path(self.temp_dir.name)
        self.assertTrue((cache_dir / "data").exists())
        self.assertTrue((cache_dir / "images").exists())

    def test_card_from_json(self):
        test_data = {
            "name": "Black Lotus",
            "id": "test-uuid",
            "set": "lea",
            "set_name": "Limited Edition Alpha",
            "collector_number": "123",
            "card_faces": [],
        }
        card = Card.from_json(test_data)
        self.assertEqual(card.name, "Black Lotus")
        self.assertEqual(card.uuid, "test-uuid")
        self.assertEqual(card.block, "lea")
        self.assertEqual(card.set_name, "Limited Edition Alpha")
        self.assertEqual(card.collector_number, "123")
        self.assertFalse(card.is_double_faced)

        # Test double-faced card
        test_data["card_faces"] = [{}, {}]
        card = Card.from_json(test_data)
        self.assertTrue(card.is_double_faced)


if __name__ == "__main__":
    unittest.main()

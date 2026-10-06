import random
import unittest

from secret_santa import Participant, draw_assignments, load_participants


class SecretSantaTests(unittest.TestCase):
    def setUp(self):
        self.participants = [
            Participant("Alex", "alex@example.com"),
            Participant("Bailey", "bailey@example.com"),
            Participant("Casey", "casey@example.com"),
            Participant("Drew", "drew@example.com"),
        ]

    def test_everyone_gets_one_distinct_recipient_and_no_self_draw(self):
        assignments = draw_assignments(self.participants, random.Random(7))

        self.assertEqual(len(assignments), len(self.participants))
        self.assertEqual({giver for giver, _ in assignments}, set(self.participants))
        self.assertEqual({recipient for _, recipient in assignments}, set(self.participants))
        self.assertTrue(all(giver != recipient for giver, recipient in assignments))

    def test_requires_at_least_two_participants(self):
        with self.assertRaises(ValueError):
            draw_assignments(self.participants[:1])

    def test_loads_csv_and_rejects_duplicate_emails(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "participants.csv"
            csv_path.write_text("name,email\nAlex,alex@example.com\nBailey,BAILEY@example.com\n", encoding="utf-8")
            self.assertEqual(len(load_participants(csv_path)), 2)

            csv_path.write_text("name,email\nAlex,alex@example.com\nAlex,ALEX@example.com\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate email"):
                load_participants(csv_path)


if __name__ == "__main__":
    unittest.main()
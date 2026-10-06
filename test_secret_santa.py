import random
import tempfile
import unittest
from pathlib import Path

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
        rng = random.Random(7)

        assignments = draw_assignments(
            self.participants,
            rng
        )

        self.assertEqual(
            len(assignments),
            len(self.participants)
        )

        givers = {
            giver
            for giver, _ in assignments
        }

        recipients = {
            recipient
            for _, recipient in assignments
        }

        self.assertEqual(
            givers,
            set(self.participants)
        )

        self.assertEqual(
            recipients,
            set(self.participants)
        )

        self.assertTrue(
            all(
                giver != recipient
                for giver, recipient in assignments
            )
        )

    def test_two_participants_receive_each_other(self):
        participants = [
            Participant("Alex", "alex@example.com"),
            Participant("Bailey", "bailey@example.com"),
        ]

        assignments = draw_assignments(
            participants,
            random.Random(1)
        )

        self.assertEqual(
            len(assignments),
            2
        )

        for giver, recipient in assignments:
            self.assertNotEqual(
                giver,
                recipient
            )

    def test_requires_at_least_two_participants(self):
        with self.assertRaisesRegex(
            ValueError,
            "At least two participants"
        ):
            draw_assignments(
                self.participants[:1]
            )

    def test_large_draw_never_assigns_someone_to_themselves(self):
        participants = [
            Participant(
                f"Person {number}",
                f"person{number}@example.com"
            )
            for number in range(100)
        ]

        assignments = draw_assignments(
            participants,
            random.Random(42)
        )

        self.assertEqual(
            len(assignments),
            100
        )

        for giver, recipient in assignments:
            self.assertNotEqual(
                giver,
                recipient
            )

        recipients = [
            recipient
            for _, recipient in assignments
        ]

        self.assertEqual(
            len(set(recipients)),
            100
        )

    def test_many_random_draws_never_produce_self_assignment(self):
        

        for seed in range(1000):

            assignments = draw_assignments(
                self.participants,
                random.Random(seed)
            )

            for giver, recipient in assignments:
                self.assertNotEqual(
                    giver,
                    recipient,
                    msg=(
                        f"Self assignment occurred "
                        f"using seed {seed}"
                    )
                )



    def test_loads_valid_csv(self):
        with tempfile.TemporaryDirectory() as directory:

            csv_path = (
                Path(directory)
                / "participants.csv"
            )

            csv_path.write_text(
                "name,email\n"
                "Alex,alex@example.com\n"
                "Bailey,bailey@example.com\n",
                encoding="utf-8"
            )

            participants = load_participants(
                csv_path
            )

            self.assertEqual(
                len(participants),
                2
            )

            self.assertEqual(
                participants[0].name,
                "Alex"
            )

            self.assertEqual(
                participants[0].email,
                "alex@example.com"
            )

    def test_rejects_duplicate_emails_case_insensitively(self):
        with tempfile.TemporaryDirectory() as directory:

            csv_path = (
                Path(directory)
                / "participants.csv"
            )

            csv_path.write_text(
                "name,email\n"
                "Alex,alex@example.com\n"
                "Another Alex,ALEX@example.com\n",
                encoding="utf-8"
            )

            with self.assertRaisesRegex(
                ValueError,
                "Duplicate email"
            ):
                load_participants(
                    csv_path
                )

    def test_rejects_missing_name(self):
        with tempfile.TemporaryDirectory() as directory:

            csv_path = (
                Path(directory)
                / "participants.csv"
            )

            csv_path.write_text(
                "name,email\n"
                ",alex@example.com\n"
                "Bailey,bailey@example.com\n",
                encoding="utf-8"
            )

            with self.assertRaises(ValueError):
                load_participants(
                    csv_path
                )

    def test_rejects_invalid_email(self):
        with tempfile.TemporaryDirectory() as directory:

            csv_path = (
                Path(directory)
                / "participants.csv"
            )

            csv_path.write_text(
                "name,email\n"
                "Alex,not-an-email\n"
                "Bailey,bailey@example.com\n",
                encoding="utf-8"
            )

            with self.assertRaises(ValueError):
                load_participants(
                    csv_path
                )

    def test_rejects_wrong_csv_headers(self):
        with tempfile.TemporaryDirectory() as directory:

            csv_path = (
                Path(directory)
                / "participants.csv"
            )

            csv_path.write_text(
                "person,address\n"
                "Alex,alex@example.com\n"
                "Bailey,bailey@example.com\n",
                encoding="utf-8"
            )

            with self.assertRaisesRegex(
                ValueError,
                "name"
            ):
                load_participants(
                    csv_path
                )

    def test_csv_requires_at_least_two_people(self):
        with tempfile.TemporaryDirectory() as directory:

            csv_path = (
                Path(directory)
                / "participants.csv"
            )

            csv_path.write_text(
                "name,email\n"
                "Alex,alex@example.com\n",
                encoding="utf-8"
            )

            with self.assertRaisesRegex(
                ValueError,
                "At least two participants"
            ):
                load_participants(
                    csv_path
                )


if __name__ == "__main__":
    unittest.main()

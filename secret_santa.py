import argparse
import csv
import os
import random
import smtplib
import ssl
import sys

from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path


@dataclass(frozen=True)
class Participant:
    name: str
    email: str


def load_participants(path: Path) -> list[Participant]:
    """
    Load and validate Secret Santa participants from a CSV file.
    """

    participants: list[Participant] = []
    seen_emails: set[str] = set()

    if not path.is_file():
        raise ValueError(f"Participant file does not exist: {path}")

    with path.open(
        mode="r",
        newline="",
        encoding="utf-8-sig"
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        if reader.fieldnames is None:
            raise ValueError("CSV file is missing a header row.")

        headers = {
            header.strip().lower()
            for header in reader.fieldnames
        }

        if headers != {"name", "email"}:
            raise ValueError(
                "CSV must contain exactly two columns: name,email"
            )

        for line_number, row in enumerate(reader, start=2):

            if None in row:
                raise ValueError(
                    f"Invalid CSV structure on line {line_number}."
                )

            values = {
                key.strip().lower(): (value or "").strip()
                for key, value in row.items()
            }

            name = values.get("name", "")
            email = values.get("email", "")

            if not name:
                raise ValueError(
                    f"Missing participant name on line {line_number}."
                )

            if (
                not email
                or "@" not in email
                or any(char.isspace() for char in email)
            ):
                raise ValueError(
                    f"Invalid email address on line {line_number}."
                )

            normalized_email = email.casefold()

            if normalized_email in seen_emails:
                raise ValueError(
                    f"Duplicate email address on line {line_number}: {email}"
                )

            seen_emails.add(normalized_email)

            participants.append(
                Participant(
                    name=name,
                    email=email
                )
            )

    if len(participants) < 2:
        raise ValueError(
            "At least two participants are required."
        )

    return participants


def draw_assignments(
    participants: list[Participant]
) -> list[tuple[Participant, Participant]]:
    """
    Randomly assign each participant exactly one recipient.

    Nobody can receive themselves.
    """

    if len(participants) < 2:
        raise ValueError(
            "At least two participants are required."
        )

    rng = random.SystemRandom()

    recipients = participants.copy()

    # Sattolo's algorithm creates one random cycle.
    #
    # This guarantees:
    # - Nobody receives themselves.
    # - Every participant is selected exactly once.
    # - No repeated shuffle/retry loop is necessary.

    for i in range(len(recipients) - 1, 0, -1):
        j = rng.randrange(i)

        recipients[i], recipients[j] = (
            recipients[j],
            recipients[i],
        )

    return list(zip(participants, recipients))


def create_message(
    giver: Participant,
    recipient: Participant,
    sender: str
) -> EmailMessage:
    """
    Create one participant's Secret Santa email.
    """

    message = EmailMessage()

    message["Subject"] = "🎄 Your Secret Santa Assignment"
    message["From"] = sender
    message["To"] = giver.email

    message.set_content(
        f"Hi {giver.name},\n\n"
        "The Secret Santa drawing is complete!\n\n"
        "Your Secret Santa recipient is:\n\n"
        f"🎁 {recipient.name} 🎁\n\n"
        "Keep their name secret!\n\n"
        "Merry Christmas! 🎄\n"
    )

    return message


def send_assignments(
    assignments: list[tuple[Participant, Participant]]
) -> None:
    """
    Send all Secret Santa assignments through SMTP.

    Assignment information is never printed.
    """

    host = os.environ.get("SMTP_HOST")
    username = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    sender = os.environ.get("SMTP_FROM") or username

    try:
        port = int(os.environ.get("SMTP_PORT", "465"))
    except ValueError as error:
        raise ValueError(
            "SMTP_PORT must be a valid integer."
        ) from error

    if not host:
        raise ValueError(
            "SMTP_HOST environment variable is missing."
        )

    if not username:
        raise ValueError(
            "SMTP_USER environment variable is missing."
        )

    if not password:
        raise ValueError(
            "SMTP_PASSWORD environment variable is missing."
        )

    if not sender:
        raise ValueError(
            "SMTP_FROM environment variable is missing."
        )

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(
        host=host,
        port=port,
        context=context,
        timeout=30
    ) as smtp:

        smtp.login(username, password)

        for giver, recipient in assignments:

            message = create_message(
                giver,
                recipient,
                sender
            )

            smtp.send_message(message)

            # Important:
            # Do NOT print recipient.name here.

            print(f"✓ Email sent to {giver.name}")


def confirm_draw(participants: list[Participant]) -> bool:
    """
    Ask the organizer for confirmation before performing
    the irreversible Secret Santa drawing.
    """

    print()
    print("Secret Santa participants:")
    print()

    for participant in participants:
        print(
            f"  • {participant.name} "
            f"<{participant.email}>"
        )

    print()
    print(f"Total participants: {len(participants)}")
    print()

    response = input(
        "Draw names and send emails? [y/N]: "
    )

    return response.strip().casefold() in {
        "y",
        "yes"
    }


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Securely draw and email Secret Santa "
            "assignments from a CSV file."
        )
    )

    parser.add_argument(
        "participants",
        type=Path,
        help=(
            "CSV file containing name and email columns"
        )
    )

    args = parser.parse_args()

    try:
        participants = load_participants(
            args.participants
        )

        if not confirm_draw(participants):
            print("Secret Santa drawing cancelled.")
            return 0

        assignments = draw_assignments(
            participants
        )

        send_assignments(
            assignments
        )

    except KeyboardInterrupt:
        print(
            "\nSecret Santa drawing cancelled.",
            file=sys.stderr
        )
        return 130

    except (
        OSError,
        ValueError,
        smtplib.SMTPException
    ) as error:

        print(
            f"\nError: {error}",
            file=sys.stderr
        )

        return 1

    print()
    print(
        f"🎄 Secret Santa assignments successfully "
        f"sent to {len(participants)} participants."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
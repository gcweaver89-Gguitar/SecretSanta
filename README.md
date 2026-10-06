# Secret Santa

A small Python command-line program that randomly assigns each participant another participant and emails the assignments privately. No one is assigned themselves, and every participant is assigned exactly once.

## Participants CSV

Create a CSV with `name` and `email` columns and at least two participants:

```csv
name,email
Alex,alex@example.com
Bailey,bailey@example.com
Casey,casey@example.com
```

## Send assignments

Configure an SMTP server using environment variables, then run the program:

```sh
export SMTP_HOST="smtp.example.com"
export SMTP_PORT="465"
export SMTP_USER="sender@example.com"
export SMTP_PASSWORD="your-smtp-password"
export SMTP_FROM="sender@example.com"
python3 secret_santa.py participants.csv
```

`SMTP_PORT` defaults to `465`; `SMTP_FROM` defaults to `SMTP_USER`. Each participant receives only their own assignment. The program does not print assignments to the terminal.

## Tests

```sh
python3 -m unittest
```

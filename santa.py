import argparse
import pickle
import random
import requests
import ssl
import sys

from email import encoders
# from emails.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from constants import API_TOKEN, SUBJECT, SENDER_EMAIL, SENDER_NAME, PARTICIPANTS, CONSTRAINTS, MSG_TEXT, MSG_HTML, PREFERENCES


# Recovery setup
PICKLE_FILE = "secret-santa.pickle"
PAIRINGS = "pairings"
CURRENT_INDEX = "curr_index"


parser = argparse.ArgumentParser()
parser.add_argument('--test', action='store_true')
args = parser.parse_args()

try:
    # Another run failed and need to be resumed
    with open(PICKLE_FILE, "rb") as f:
        pickled_data = pickle.load(f)
        pairings = pickled_data[PAIRINGS]
        current_index = pickled_data[CURRENT_INDEX]
        print(f'Recovered pairings successfully. Current index is {current_index}')

except FileNotFoundError:
    # Draw the pairings and retry until constraints are satisfied
    participants_names = list(PARTICIPANTS.keys())
    pairings = {}
    pairings_ok = False

    while not pairings_ok:
        pairings_ok = True

        print("(re)trying")
        random.shuffle(participants_names)

        for i, person in enumerate(participants_names):
            gift_to = participants_names[(i+1) % len(participants_names)]

            if CONSTRAINTS.get(person) and gift_to not in CONSTRAINTS[person]:
                pairings_ok = False
                break

            pairings[person] = gift_to


if args.test:
    # Only print a potential pairing and exit
    print('A possible pairing is:')
    for g, v in pairings.items():
        print(f'{g}: {v}')
    sys.exit(0)

sys.exit(0)

current_index = 0

url = "https://send.api.mailtrap.io/api/send"

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Api-Token": API_TOKEN,
}

# Send the emails
for giver, gift_recipient in pairings.items():
    giver_email = PARTICIPANTS[giver]

    if not giver_email:
        raise ValueError("Empty email address!")

    preferences = "Aucune indication" if giver not in PREFERENCES else PREFERENCES[giver]

    payload = {
        "subject": SUBJECT,
        "from": {
            "email": SENDER_EMAIL,
            "name": SENDER_NAME,
        },
        "to": [
            {
                "email": giver_email,
                "name": giver,
            }
        ],
        "text": MSG_TEXT.format(giver, gift_recipient, preferences),
        "html": MSG_HTML.format(giver, gift_recipient, preferences),
    }

    try:
        response = requests.post(url, json=payload, headers=headers)

    except Exception as e:
        print(e)

        with open(PICKLE_FILE, "wb") as f:
            pickle.dump({PAIRINGS: pairings, CURRENT_INDEX: current_index}, f)

        raise e

    print(response, response.content)
    current_index += 1

from auth import fetch_cards, is_authorized, request_code, verify_code
from getpass import getpass
import logging
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
from threading import Thread
from time import sleep


pepper = getpass("Enter pepper. You will not see the characters you type: ")

logging.basicConfig(
    filename="kagi.log",
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)

reader = SimpleMFRC522()
try:
    print("Program started! There will be no further output other than errors from now on!")

    # Start routine fetching of cards from database on a separate thread
    card_fetcher = Thread(target=fetch_cards, daemon=True)
    card_fetcher.start()

    # Card reading loop
    while True:
        try:
            card_id, text = reader.read()
            card_id = str(card_id)
        except Exception as e:
            logging.warning(e)
            continue
        else:
            # beep sound + light
            if card_id:
                if is_authorized(card_id):
                    code = request_code()
                    access = verify_code(card_id, code, pepper)
                else:
                    access = False

                if access:
                    pass
                    # Open keybox
                else:
                    pass
                    # light
            else:
                logging.warning("DENIED | null | No card id")

            sleep(5)  # 5 second timeout after successfull reading of card
finally:
    GPIO.cleanup()

import auth
from getpass import getpass
import logging
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
from threading import Thread
from time import sleep


if __name__ == "__main__":
    pepper = getpass("Enter pepper. You will not see the characters you type: ")

    logging.basicConfig(
        filename="kagi.log",
        format="%(asctime)s | %(levelname)s | %(message)s",
        level=logging.INFO
    )

    reader = SimpleMFRC522()

    logging.info("PROGRAM | Program launched!")
    print("Program started! There will be no further output other than errors from now on!")

    try:
        # Start routine fetching of cards from database on a separate thread
        card_fetcher = Thread(target=auth.fetch_cards, daemon=True)
        card_fetcher.start()

        # Card reading loop
        while True:
            try:
                card_id, _ = reader.read()
                card_id = str(card_id)
            except Exception as e:
                logging.warning(e)
                continue

            if not card_id:
                logging.warning("DENIED | null | No card id")
                continue

            # beep sound + light

            if auth.is_authorized(card_id):
                code = auth.request_code()
                access = auth.verify_code(card_id, code, pepper)
            else:
                access = False

            if not access:
                logging.warning(f"DENIED | {card_id} | Incorrect code")
                # denied sound + light
                sleep(5)
                continue

            if auth.is_admin(card_id):
                logging.info("REGISTER PEDING | Admin card registering new card")
                auth.register_card(pepper)
            else:
                pass
                # granted sound + light
                # Open keybox
    finally:
        GPIO.cleanup()

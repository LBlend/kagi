import bcrypt
from dotenv import load_dotenv
import keyboard
import logging
import multiprocessing
import os
import psycopg2
from time import sleep


load_dotenv()

connection = psycopg2.connect(
    host=os.getenv("KAGI_DB_HOST"),
    dbname=os.getenv("KAGI_DB_NAME"),
    user=os.getenv("KAGI_DB_USERNAME"),
    password=os.getenv("KAGI_DB_PASSWORD")
)

codes = {}


def fetch_cards() -> None:
    cursor = connection.cursor()
    timer = float("inf")  # Init as infinite to trigger db fetch at first run

    while True:
        if timer < 600:  # 10 minutes
            sleep(1)
            timer += 1
        else:
            try:
                cursor.execute(
                    """
                    SELECT id, code
                    FROM cards
                    """
                )
                cards = cursor.fetchall()
            except Exception as e:
                logging.error(e.strip("\n"))
            else:
                for card in cards:
                    codes[card[0]] = card[1]
                logging.info("PROGRAM | Passcodes fetched from database")
            finally:
                timer = 0


def is_authorized(card_id: str) -> bool:
    if card_id in codes.keys():
        logging.info(f"PENDING | {card_id} | Waiting for passcode")
        return True

    logging.info(f"DENIED | {card_id} | Not a valid card")
    return False


def request_code() -> list[str]:
    # Initialize shared array
    code = multiprocessing.Array("u", ["a"]*4)

    # Fetch stdin. Time out if code is not entered within 10 seconds
    input_proc = multiprocessing.Process(target=_get_input, args=(code,))
    input_proc.start()
    input_proc.join(10)
    input_proc.terminate()

    # Convert Multiprocessing array to an actual array
    return code[:]


def verify_code(card_id: str, code: list[str], pepper: str) -> bool:
    if "a" in code:  # Check if code was fully entered
        logging.info(f"DENIED | {card_id} | Passcode timeout")
        return False

    try:
        code = int("".join(code))
    except ValueError:
        logging.info(f"DENIED | {card_id} | Not a numbered code")
        return False
    else:
        code = (str(code) + pepper).encode("utf-8")

        if bcrypt.checkpw(code, codes.get(card_id).encode("utf-8")):
            logging.info(f"GRANTED | {card_id} | Access granted")
            return True
        else:
            logging.info(f"DENIED | {card_id} | Invalid passcode")
            return False


def _get_input(code: dict[str, str]) -> None:
    character = 0
    while character < 4:
        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN:
            os.system("cls" if os.name == "nt" else "clear")  # Clear user input from console output
            # beep sound
            code[character] = event.name
            character += 1

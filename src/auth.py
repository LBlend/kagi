import bcrypt
from ctypes import c_int64
from database import Database
import keyboard
import logging
from mfrc522 import SimpleMFRC522
import multiprocessing
import RPi.GPIO as GPIO
import os
from time import sleep


db = Database()
db.init_db()

salt = bcrypt.gensalt()

codes = {}


def fetch_cards() -> None:
    timer = float("inf")  # Init as infinite to trigger db fetch at first run

    while True:
        if timer < 600:  # 10 minutes
            sleep(1)
            timer += 1
        else:
            update_local_codes_index()
            timer = 0


def update_local_codes_index():
    cards = db.fetch_cards()

    # In order to mutate the global codes variable we need to assign this way, even though it sucks
    codes.clear()
    for card_id, code in cards.items():
        codes[card_id] = code
    logging.info("PROGRAM | Passcodes fetched from database")


def is_admin(card_id) -> bool:
    return db.is_admin(card_id)


def is_authorized(card_id: str) -> bool:
    if card_id in codes.keys():
        logging.info(f"PENDING | {card_id} | Waiting for passcode")
        return True

    logging.info(f"DENIED | {card_id} | Not a valid card")
    return False


def __register_card_read(value_holder: multiprocessing.Value):
    reader = SimpleMFRC522()
    card_id, _ = reader.read()
    value_holder.value = card_id


def register_card(pepper: str):
    while True:
        try:
            # Fetch card_id. Time out if card is not read within 10 seconds
            card_id_holder = multiprocessing.Value(c_int64, 0)
            card_read = multiprocessing.Process(target=__register_card_read, args=(card_id_holder,))
            card_read.start()
            card_read.join(10)
            card_read.terminate()

            if card_id_holder.value != 0:
                card_id = str(card_id_holder.value)
            else:
                card_id = None
        except Exception as e:
            logging.warning(f"Failed to read card to be registrated - {e}")
            continue
        else:
            if not card_id:
                logging.info("REGISTER DENIED | Failed to register new card")
                # beep sound + red light
                break

            # beep sound + light
            logging.info(f"REGISTER PENDING | {card_id}")
            code = request_code()

            # Check if code was fully entered
            if "a" in code:
                logging.info(f"REGISTER DENIED | {card_id} | Code was not input")
                # beep sound + red light
                break
            else:
                # beep sound + yellow light
                passcode = str.encode(code + pepper)
                hashed = bcrypt.hashpw(passcode, salt).decode("utf-8")

                db.add_card(card_id, hashed)
                logging.info(f"REGISTER SUCCESS | {card_id}")
                update_local_codes_index()
                # beep sound  + Green light
                break
        finally:
            GPIO.cleanup()
            return


def request_code() -> list[str]:
    # Initialize shared array
    code = multiprocessing.Array("u", ["a"]*4)

    # Fetch stdin. Time out if code is not entered within 10 seconds
    input_proc = multiprocessing.Process(target=__get_input, args=(code,))
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

    code = (str(code) + pepper).encode("utf-8")

    if bcrypt.checkpw(code, codes.get(card_id).encode("utf-8")):
        logging.info(f"GRANTED | {card_id} | Access granted")
        return True

    logging.info(f"DENIED | {card_id} | Invalid passcode")
    return False


def __get_input(code: dict[str, str]) -> None:
    character = 0
    while character < 4:
        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN:
            os.system("cls" if os.name == "nt" else "clear")  # Clear user input from console output
            # beep sound
            code[character] = event.name
            character += 1

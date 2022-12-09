from dotenv import load_dotenv
import logging
import os
import psycopg2


class Database:
    def __init__(self):
        load_dotenv()
        self.connection = psycopg2.connect(
            host=os.getenv("KAGI_DB_HOST"),
            dbname=os.getenv("KAGI_DB_NAME"),
            user=os.getenv("KAGI_DB_USERNAME"),
            password=os.getenv("KAGI_DB_PASSWORD")
        )

    def init_db(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS public.cards (
                id text NOT NULL PRIMARY KEY,
                code text NOT NULL,
                holder text,
                is_admin boolean DEFAULT false NOT NULL,
                last_updated timestamp without time zone DEFAULT now() NOT NULL
            );

            ALTER TABLE public.cards OWNER TO kagi;

            GRANT SELECT,INSERT,UPDATE ON TABLE public.cards TO kagi;
            """
        )
        self.connection.commit()

    def fetch_cards(self) -> dict[str, str]:
        codes = {}

        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """
                SELECT id, code
                FROM cards;
                """
            )
            cards = cursor.fetchall()
        except Exception as e:
            logging.error(e.strip("\n"))
            return codes

        for card in cards:
            codes[card[0]] = card[1]

        return codes

    def add_card(self, card_id: str, passcode: str, holder: str = None, is_admin: bool = False) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO cards (id, code, holder, is_admin, last_updated)
            VALUES (%s, %s, %s, %s, now())
            ON CONFLICT (id)
            DO
                UPDATE SET code = EXCLUDED.code, holder = EXCLUDED.holder, is_admin = EXCLUDED.is_admin, last_updated = EXCLUDED.last_updated;
            """, (card_id, passcode, holder, is_admin)  # TODO: Passing the same value twice is dumb. Fix this
        )
        self.connection.commit()

    def is_admin(self, card_id: str) -> bool:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT is_admin
            FROM cards
            WHERE id = (%s);
            """, (card_id,)
        )

        if result := cursor.fetchone():
            result = result[0]

        if result:
            return True
        return False

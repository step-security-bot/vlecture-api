from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from openai import OpenAI
from pydantic import UUID4

from starlette.status import HTTP_400_BAD_REQUEST

from src.models.flashcards import Flashcard, FlashcardSet
from src.schemas.flashcards import GenerateFlashcardRequestSchema
from src.utils.openai import construct_system_flashcard_instructions
from src.utils.db import get_db

from src.utils.settings import (
    OPENAI_API_KEY,
    OPENAI_ORG_ID,
    OPENAI_MODEL_NAME,
)


class FlashcardService:
    MODEL_TEMPERATURE = 0.7

    def __init__(self) -> None:
        # Init OpenAI Client
        self.openai_client = OpenAI(
            api_key=OPENAI_API_KEY,
            organization=OPENAI_ORG_ID,
        )

    def get_openai(self):
        return self.openai_client

    def generate_flashcard_sets(self, payload: GenerateFlashcardRequestSchema):
        if self.check_word_count(payload.main_word_count, payload.num_of_flashcards):
            client = self.get_openai()
            context = self.extract_text(payload.main)
            SYSTEM_PROMPT = construct_system_flashcard_instructions(
                context=context,
                num_of_flashcards=payload.num_of_flashcards,
                language=payload.language,
            )

            chat_completion = client.chat.completions.create(
                model=OPENAI_MODEL_NAME,
                temperature=self.MODEL_TEMPERATURE,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    }
                ],
            )
            return chat_completion

    def get_flashcard_sets_by_user(
        self, user_id: UUID4, session: Session = Depends(get_db)
    ):
        flashcard_sets = (
            session.query(FlashcardSet)
            .filter(FlashcardSet.user_id == user_id, FlashcardSet.is_deleted == False)
            .all()
        )

        return self.build_json_flashcard_sets(flashcard_sets)

    def get_flashcards_by_set(self, session: Session, set_id: UUID4, note_id: UUID4):
        flashcards = (
            session.query(Flashcard)
            .filter(
                Flashcard.set_id == set_id,
                Flashcard.note_id == note_id,
                Flashcard.is_deleted == False,
            )
            .all()
        )

        return self.build_json_flashcards(flashcards)

    def build_json_flashcard_sets(self, flashcard_sets):
        data = []
        for flashcard_set in flashcard_sets:
            item = {
                "set_id": flashcard_set.set_id,
                "note_id": flashcard_set.note_id,
                "user_id": flashcard_set.user_id,
                "title": flashcard_set.title,
                "date_generated": flashcard_set.date_generated,
                "tags": flashcard_set.tags,
                "is_deleted": flashcard_set.is_deleted,
            }
            data.append(item)

        return data

    def build_json_flashcards(self, flashcards):
        data = []
        for flashcard in flashcards:
            item = {
                "flashcard_id": flashcard.flashcard_id,
                "set_id": flashcard.set_id,
                "note_id": flashcard.note_id,
                "front": flashcard.front,
                "back": flashcard.back,
                "is_deleted": flashcard.is_deleted,
                "rated_difficulty": flashcard.rated_difficulty,
            }
            data.append(item)

        return data

    def get_set_owner(self, set_id, session):
        set = (
            session.query(FlashcardSet)
            .filter(FlashcardSet.set_id == set_id, FlashcardSet.is_deleted == False)
            .one()
        )

        return set.user_id

    # Helper Functions

    def check_word_count(self, word_count, num_of_flashcards):
        if word_count // 50 < num_of_flashcards:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST, detail="Note too short!"
            )
        else:
            return True

    def extract_text(self, main):
        text = ""
        for i, element in enumerate(main):
            text += element.content.text + " "
        return text

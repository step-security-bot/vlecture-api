from enum import Enum
import http
from datetime import datetime

from fastapi import (
    APIRouter,
    Request,
    Depends,
    Body,
)

from fastapi.responses import JSONResponse

from src.models.users import User

from src.schemas.qna import (
  # OBJECTS
  QNAQuestionSetSchema,
  QNASetReviewSchema,
  QNASetReviewPayloadSchema,

  # REQUESTS
  GenerateQNASetRequestSchema,
)

 
from src.services.users import get_current_user

from src.services.note import (
  NoteService
)

from src.services.qna import (
  QNAService
)

class QNARouterTags(Enum):
  qna = "qna"

qna_router = APIRouter(
  prefix="/v1/qna",
  tags=[QNARouterTags.qna],
)

@qna_router.post(
  "/generate",
  response_description="Create a new Note QnA set",
  status_code=http.HTTPStatus.OK,
  response_model=QNAQuestionSetSchema,
)
def generate_qna_set(
  request: Request,
  payload: GenerateQNASetRequestSchema = Body(),
  user: User = Depends(get_current_user),
):
  note_service = NoteService()
  qna_service = QNAService()

  note_id = payload.note_id
  question_count = payload.question_count
  
  my_note = note_service.fetch_note_from_mongodb(
    note_id=note_id,
    request=request,
    user=user,
  )

  generated_qna_set = qna_service.generate_qna_set(
    note=my_note,
    question_count=question_count,
  )

  created_qna_set_schema = qna_service.create_qna_set_obj(
    question_count=question_count,
    note_id=note_id,
    qna_set=generated_qna_set,
    user=user,
  )

  # Store to MongoDB
  new_qna_set_document = request.app.qna_collection.insert_one(
    created_qna_set_schema.model_dump(
      by_alias=True,
      exclude=["id"],
    )
  )

  created_qna_set_document = request.app.qna_collection.find_one({
    "_id": new_qna_set_document.inserted_id,
  })

  return created_qna_set_document

@qna_router.get(
  "/{note_id}",
  response_description="Fetch a QnA Set for a specific Note",
  status_code=http.HTTPStatus.OK,
  response_model=QNAQuestionSetSchema,
)
def get_qna_set_by_note(
    note_id: str,
    request: Request,
    user: User = Depends(get_current_user),
):
  qna_service = QNAService()
  
  my_qna_set = qna_service.fetch_qna_set_from_note(
    note_id=note_id,
    request=request,
    user=user,
  )

  return my_qna_set

@qna_router.post(
  "/review",
  status_code=http.HTTPStatus.CREATED,
  response_model=QNASetReviewSchema,
)
def review_qna(
  request: Request,
  payload: QNASetReviewPayloadSchema = Body(),
  user: User = Depends(get_current_user),
):
  qna_service = QNAService()

  review_qna_response = qna_service.review_qna(
    request=request,
    payload=payload
  )

  qna_review_result = request.app.qna_results_collection.find_one({
      "note_id": payload.note_id,
      "owner_id": user.id,
      "is_deleted": False
    })

  if qna_review_result:
    qna_review_result["is_deleted"] = True
    updated_qna_review_result = request.app.qna_results_collection.find_one_and_update(
      {
        "note_id": payload.note_id,
        "owner_id": user.id,
        "is_deleted": False
      },
      {
        "$set": qna_review_result
      }
    )

  # Store to MongoDB
  new_review_qna_document = request.app.qna_results_collection.insert_one(
    review_qna_response.model_dump(
      by_alias=True,
      exclude=["id"],
    )
  )

  created_review_qna_document = request.app.qna_results_collection.find_one({
    "_id": new_review_qna_document.inserted_id,
  })

  if created_review_qna_document:
    return JSONResponse(
      status_code=http.HTTPStatus.CREATED, 
      content={"message": "Created: QNA Review Result successfully created."}
    )
  else:
    return JSONResponse(
      status_code=http.HTTPStatus.BAD_REQUEST, 
      content={"message": "BadRequest: Internal Server Error."}
    )

@qna_router.get(
  "/review/{note_id}",
  status_code=http.HTTPStatus.OK,
  response_model=QNASetReviewSchema,
)
def get_qna_review_result_by_note_id(
    note_id: str,
    request: Request,
    user: User = Depends(get_current_user),
):
  qna_service = QNAService()

  qna_review_result = qna_service.fetch_qna_review_result_from_mongodb(
    note_id=note_id,
    request=request,
    user=user,
  )

  if not qna_review_result:
    return JSONResponse(
      status_code=http.HTTPStatus.NOT_FOUND, 
      content={"message": "NotFound: QNA Review Result not found or already deleted."}
    )

  return qna_review_result
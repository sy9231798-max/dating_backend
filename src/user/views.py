from typing import List

from fastapi import APIRouter, Header, Depends, HTTPException
from fastapi.params import Body, Query
from sqlmodel import Session
from starlette import status

from src.pagination_model import PaginatedResponse
from src.auth.model_wrapper import LoginResponseWrapper
from src.database import get_session
from src.mongo_helper import message_collection
from src.user.model_wrapper import UserDataResponse, ConversationDataResponse, MessageResponse, CallDataResponse, \
    PaymentRequestResponse
from src.user.service import (get_my_information, fetch_explore, fetch_profile_status, fetch_conversation,
                              fetch_all_message, sent_request, friend_request_action, fetch_call_history, blocked_user,
                              unblocked_user, report_user, call_availability_check, fetch_stored_payment_detail,
                              add_store_payment_detail, remove_store_payment_detail, fetch_all_payment_history,
                              create_withdraw_request, fetch_payment_history, fetch_lifetime_earning)
from src.user.models import UserPaymentDetail, UserPaymentHistory

router = APIRouter()


@router.get("/me", response_model=UserDataResponse)
async def get_me_information(
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return get_my_information(db=db, token=user_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed get my information: {str(e)}"
        )


@router.get("/profile-status", response_model=LoginResponseWrapper)
async def get_profile_status(
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return fetch_profile_status(db=db, token=user_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile-status: {str(e)}"
        )


@router.get("/explore", response_model=List[UserDataResponse])
async def get_explore_data(
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return fetch_explore(db=db, token=user_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch explore: {str(e)}"
        )


@router.get("/conversation", response_model=List[ConversationDataResponse])
async def get_conversation_data(
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return fetch_conversation(db=db, token=user_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversation: {str(e)}"
        )


@router.get("/messages/{conversation_id}", response_model=List[MessageResponse])
async def get_conversation_data(
        conversation_id: int,
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return await fetch_all_message(token=user_token, conversation_id=conversation_id,
                                       message_collection=message_collection, db=db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch message: {str(e)}"
        )


@router.get("/check-call/{receiver_id}")
def check_call_availability(
        receiver_id: int,
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return call_availability_check(
            token=user_token,
            db=db,
            receiver_id=receiver_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to call availability check: {str(e)}"
        )


@router.get("/call-history", response_model=List[CallDataResponse])
async def get_call_history(
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return fetch_call_history(db=db, token=user_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversation: {str(e)}"
        )


@router.get("/send-request")
async def send_request(
        friend_id: int,
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return sent_request(
            friend_id=friend_id,
            token=user_token,
            db=db
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch message: {str(e)}"
        )


@router.get("/friend-request-response")
async def friend_request_response(
        request_id: int,
        is_accepted: bool,
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:

        return friend_request_action(
            is_accept=is_accepted,
            request_id=request_id,
            token=user_token,
            db=db,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update friend request: {str(e)}"
        )


@router.get("/blocked-request/{user_id}")
async def blocked_request(
        user_id: int,
        reason: str = Body(...),
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:

        return blocked_user(db=db, token=user_token, blocked_id=user_id, reason=reason)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to block user: {str(e)}"
        )


@router.get("/unblocked-request/{id}")
async def unblocked_request(
        id: int,
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:

        return unblocked_user(db=db, token=user_token, blocked_id=id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unblock user: {str(e)}"
        )


@router.get("/report-user/{user_id}")
async def report_request(
        user_id: int,
        reason: str = Body(...),
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return report_user(db=db, token=user_token, reported_id=user_id, reason=reason)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to report user: {str(e)}"
        )


@router.get("/payment-history", response_model=List[UserPaymentHistory])
async def get_all_payment_history(
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return fetch_all_payment_history(db=db, token=user_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payment history: {str(e)}"
        )


@router.get("/stored-payment-detail")
async def stored_payment_detail(
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return fetch_stored_payment_detail(db=db, token=user_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stored payment detail: {str(e)}"
        )


@router.post("/store-payment-detail", response_model=UserPaymentDetail)
async def store_payment_detail(
        payment_detail: PaymentRequestResponse,
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return add_store_payment_detail(db=db, token=user_token, payment_detail=payment_detail)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stored payment detail: {str(e)}"
        )


@router.delete("/delete-store-payment-detail", response_model=UserPaymentDetail)
async def delete_store_payment_detail(
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return remove_store_payment_detail(db=db, token=user_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete stored payment detail: {str(e)}"
        )


@router.get("/lifetime-earning")
async def withdraw_request(
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return fetch_lifetime_earning(db=db, token=user_token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get lifetime earning: {str(e)}"
        )


@router.get("/get-withdraw-history",response_model=PaginatedResponse[UserPaymentHistory])
async def get_withdraw_history(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return fetch_payment_history(db=db, token=user_token,page_item=page_size,page=page)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get withdraw history: {str(e)}"
        )


@router.post("/withdrawal-request")
async def withdraw_request(
        amount: int = Body(..., gt=0),
        user_token: str = Header(None, convert_underscores=True, alias="UserToken"),
        db: Session = Depends(get_session),
):
    try:
        return create_withdraw_request(db=db, token=user_token, amount=amount)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to make withdraw request: {str(e)}"
        )

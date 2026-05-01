from typing import Optional

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection
from sqlalchemy.orm import selectinload, aliased
from sqlmodel import Session, select, or_, desc
from starlette import status

from src.instance_handler import get_chat_handler
from src.auth.model_wrapper import LoginResponseWrapper
from src.token_helper import verify_token, create_token
from src.user.model_wrapper import ConversationDataResponse, MessageResponse, CallDataResponse
from src.user.models import UserModel, AccountType, ConversationTable, FriendTable, FriendRequestTable, \
    CallHistory, BlockedUser, ReportUser, CallHistory
from src.video_sdk_helper import get_room_id


def get_my_information(
        token: str,
        db: Session
):
    try:
        payload = verify_token(token)
        user_id = payload["user_id"]
        db_user = db.get(UserModel, user_id)
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )

        return db_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


def fetch_profile_status(
        token: str,
        db: Session
):
    try:
        payload = verify_token(token)
        user_id = payload["user_id"]
        db_user: Optional[UserModel] = db.get(UserModel, user_id)
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        any_error = (
                db_user.step_1_error not in ["PENDING", "DONE"]
                or db_user.step_2_error not in ["PENDING", "DONE"]
                or db_user.step_3_error not in ["PENDING", "DONE"]
        )
        all_pending = (
                db_user.step_1_error in ["PENDING"]
                and db_user.step_2_error in ["PENDING"]
                and db_user.step_3_error in ["PENDING"]
        )
        if all_pending:
            error_code = status.HTTP_404_NOT_FOUND
        elif any_error:
            error_code = status.HTTP_400_BAD_REQUEST
        else:
            error_code = status.HTTP_200_OK
        return LoginResponseWrapper(
            user_data=db_user,
            token=create_token(db_user, isClient=True),
            error_code=error_code,
            addition_image=db_user.addition_images,
            step2_error_message=db_user.step_2_error,
            step3_error_message=db_user.step_3_error,
            step1_error_message=str(db_user.step_1_error)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


def call_availability_check(
        token: str,
        receiver_id: int,
        db: Session
):
    try:
        payload = verify_token(token)
        user_id = payload["user_id"]

        is_available = get_chat_handler().available_for_call(receiver_id)
        if not is_available[0]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=is_available[1]
            )

        roomId = get_room_id()
        call_history = CallHistory()
        call_history.room_id = roomId
        call_history.caller_id = user_id
        call_history.receiver_id = receiver_id
        db.add(call_history)
        db.commit()
        return {
            "roomId": roomId,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check call availability: {str(e)}"
        )


def fetch_explore(
        token: str,
        db: Session
):
    try:
        # payload = verify_token(token)
        # user_id = payload["user_id"]
        user_id = 1
        # b1 = aliased(BlockedUser)
        # b2 = aliased(BlockedUser)
        # statement = (select(UserModel)
        #              .outerjoin(b1, and_(
        #     b1.blocked_id == UserModel.id,
        #     b1.blocker_id == user_id
        # ))
        #              .outerjoin(b2, and_(
        #     b2.blocker_id == UserModel.id,
        #     b2.blocked_id == user_id
        # ))
        #              .where(UserModel.account_type == AccountType.AGENT)
        # .options(selectinload(UserModel.addition_images))
        # .order_by(desc(UserModel.score)))
        # users = db.exec(statement).all()
        users = db.query(UserModel).options(selectinload(UserModel.addition_images)).order_by(
            desc(UserModel.score)).all()
        return users
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


def fetch_conversation(
        token: str,
        db: Session
):
    try:
        payload = verify_token(token)
        user_id = payload["user_id"]
        statement = select(ConversationTable).where(
            or_(
                ConversationTable.user_a_id == user_id,
                ConversationTable.user_b_id == user_id
            )
        ).order_by(desc(ConversationTable.created_at))
        all_conversation = db.exec(statement).all()
        return [ConversationDataResponse.conversation(user_id=user_id, conversation=i) for i in all_conversation]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


def fetch_call_history(
        token: str,
        db: Session
):
    try:
        payload = verify_token(token)
        user_id = payload["user_id"]
        statement = (select(CallHistory).where(
            or_(
                CallHistory.caller_id == user_id,
                CallHistory.receiver_id == user_id
            )
        ).options(
            selectinload(CallHistory.caller),
            selectinload(CallHistory.receiver)
        ).
                     order_by(desc(CallHistory.created_at)))
        all_call_history = db.exec(statement).all()
        return [CallDataResponse.call_history(user_id=user_id, call_history=i) for i in all_call_history]
        # return [ConversationDataResponse.conversation(user_id=user_id, conversation=i) for i in all_conversation]
        return all_call_history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to Login: {str(e)}"
        )


def serialize_message(message):
    message["_id"] = str(message["_id"])
    return message


async def fetch_all_message(
        token: str,
        message_collection: AsyncIOMotorCollection,
        db: Session,
        conversation_id: int,
):
    try:
        payload = verify_token(token)
        user_id = payload["user_id"]

        db_conversation: Optional[ConversationTable] = db.exec(
            select(ConversationTable).where(ConversationTable.id == conversation_id)).first()

        if db_conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation with id {conversation_id} not found"
            )

        if db_conversation.user_a_id != user_id and db_conversation.user_b_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This Conversation not belong to you"
            )

        messages = await message_collection.find({
            "conversation_id": conversation_id,
        }).sort("send_at", -1).to_list(length=None)

        print(f"Message Length {len(messages)} ${messages[0]}")
        return [MessageResponse.from_mongodb(msg) for msg in messages]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch all message: {str(e)}"
        )


def sent_request(
        friend_id: int,
        token: str,
        db: Session,
):
    try:
        payload = verify_token(token)
        user_id = payload["user_id"]

        db_user: Optional[UserModel] = db.exec(select(UserModel.id == user_id)).first()
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )

        db_friend: Optional[UserModel] = db.exec(select(UserModel.id == friend_id)).first()
        if db_friend is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Friend id not found"
            )

        friend_request = FriendRequestTable(
            sender_id=user_id,
            receiver_id=friend_id,
        )

        db.add(friend_request)
        db.commit()
        return {
            "message": "Friend request sent",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sent friend request: {str(e)}"
        )


def friend_request_action(
        is_accept: bool,
        request_id: int,
        token: str,
        db: Session,
):
    try:
        payload = verify_token(token)
        user_id = payload["user_id"]

        db_request: Optional[FriendRequestTable] = db.exec(
            select(FriendRequestTable).where(FriendRequestTable.id == request_id)).first()
        if db_request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Friend request might be cancel by sender"
            )

        if db_request.receiver_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This friend request not belong to you"
            )

        if is_accept:
            db.add(FriendTable(
                user_id=db_request.sender_id,
                friend_id=db_request.receiver_id,
            ))
            db.add(FriendTable(
                friend_id=db_request.sender_id,
                user_id=db_request.receiver_id,
            ))

        db.delete(db_request)
        db.commit()
        return {
            "message": "You are friend now" if is_accept else "Friend request removed"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update friend request: {str(e)}"
        )


def blocked_user(
        blocked_id: int,
        reason: str,
        token: str,
        db: Session,
):
    try:
        payload = verify_token(token)
        user_id = payload["user_id"]

        db_user: Optional[UserModel] = db.exec(select(UserModel.id == blocked_id)).first()
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found"
            )

        db_block = BlockedUser()
        db_block.blocker_id = user_id
        db_block.blocked_id = blocked_id
        db_block.reason = reason
        db.add(db_block)
        db.commit()
        db.refresh(db_block)
        return {
            "message": "Blocked user",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to block user: {str(e)}"
        )


def unblocked_user(
        blocked_id: int,
        token: str,
        db: Session,
):
    try:
        payload = verify_token(token)
        user_id = payload["user_id"]

        db_block: Optional[BlockedUser] = db.exec(select(BlockedUser).where(BlockedUser.id == blocked_id)).first()
        if db_block is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"blocked information not found"
            )

        if db_block.blocker_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This blocked user not belong to you"
            )

        db.delete(db_block)
        return {
            "message": "User unblocked",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unblock user: {str(e)}"
        )


def report_user(
        reported_id: int,
        reason: str,
        token: str,
        db: Session,
):
    try:
        payload = verify_token(token)
        user_id = payload["user_id"]

        db_user: Optional[UserModel] = db.exec(select(UserModel.id == reported_id)).first()
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found"
            )

        db_report = ReportUser()
        db_report.reporter_id = user_id
        db_report.reported_id = reported_id
        db_report.reason = reason
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        return {
            "message": "User reported",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to report user: {str(e)}"
        )

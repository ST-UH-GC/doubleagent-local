import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, status, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.chatbot import ChatbotService
from app.db.database import DBSession, engine
from app.db.models import Base
from sqlalchemy.orm import Session
from app import schemas
from app.db import models
from sqlalchemy import select, update
import asyncio
from fastapi.responses import StreamingResponse
import json

load_dotenv()

app = FastAPI()

# Create database tables on startup (SQLite, no migrations needed)
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_user() -> dict:
    return {"sub": "local-user", "name": "Local User"}


def get_user_id() -> str:
    return "local-user"


chatbot_a = ChatbotService()
chatbot_b = ChatbotService()

messages: list[str] = []


class Message(BaseModel):
    text: str


class ChatMessage(BaseModel):
    message: str
    thread_id: str = "default"
    system_prompt: str | None = None
    model: str | None = None
    chatbot: str = "a"


class ChatResponse(BaseModel):
    user_message: str
    ai_response: str
    thread_id: str
    chatbot: str
    model_used: str | None = None


class ConversationStart(BaseModel):
    initial_message: str
    system_prompt_a: str | None = None
    system_prompt_b: str | None = None
    thread_id: str = "default"
    turns: int = 6
    model: str | None = None
    history: list[dict] | None = None


class ConversationResponse(BaseModel):
    messages: list[dict]


@app.post("/chat", response_model=ChatResponse)
def chat_with_bot(
    chat_msg: ChatMessage, current_user: dict = Depends(get_current_user)
):
    if chat_msg.chatbot == "b":
        chatbot = chatbot_b
    else:
        chatbot = chatbot_a

    ai_response = chatbot.chat(
        chat_msg.message,
        chat_msg.thread_id,
        chat_msg.system_prompt,
        chat_msg.model,
    )
    return ChatResponse(
        user_message=chat_msg.message,
        ai_response=ai_response,
        thread_id=chat_msg.thread_id,
        chatbot=chat_msg.chatbot,
    )


async def conversation_generator(conv: ConversationStart, request: Request):
    print(f"\n--- 🚀 STARTING TOKEN STREAM for {conv.turns} turns ---")
    print(f"--- 📝 Thread ID: {conv.thread_id} ---")
    current_message = conv.initial_message
    current_bot = "a"
    if conv.history and isinstance(conv.history, list) and len(conv.history) > 0:
        parts = []
        for m in conv.history:
            role = m.get("chatbot")
            text = m.get("message", "")
            if role == "user":
                parts.append(f"User: {text}")
            else:
                parts.append(f"Chatbot {role.upper()}: {text}")

        context_str = "\n".join(parts)
        current_message = context_str + "\n\n" + conv.initial_message

        last = conv.history[-1].get("chatbot")
        if last == "a":
            current_bot = "b"
        elif last == "b":
            current_bot = "a"
        else:
            current_bot = "a"

    if conv.system_prompt_a:
        chatbot_a.set_system_prompt(conv.system_prompt_a)
    else:
        chatbot_a.set_system_prompt(chatbot_a.default_system_prompt)

    if conv.system_prompt_b:
        chatbot_b.set_system_prompt(conv.system_prompt_b)
    else:
        chatbot_b.set_system_prompt(chatbot_b.default_system_prompt)

    try:
        for i in range(conv.turns):
            if await request.is_disconnected():
                print("--- 🛑 Client disconnected, stopping stream. ---")
                break

            print(f"--- Stream Turn {i+1} ---")

            chatbot_instance = chatbot_a if current_bot == "a" else chatbot_b

            start_data = {"type": "start", "chatbot": current_bot}
            yield f"data: {json.dumps(start_data)}\n\n"

            full_response_for_next_turn = ""

            async for token in chatbot_instance.stream_chat(
                current_message,
                conv.thread_id,
                model=conv.model,
            ):
                token_data = {"type": "token", "content": token}
                yield f"data: {json.dumps(token_data)}\n\n"

                full_response_for_next_turn += token

            end_data = {"type": "end"}
            yield f"data: {json.dumps(end_data)}\n\n"

            current_message = full_response_for_next_turn
            current_bot = "b" if current_bot == "a" else "a"

            await asyncio.sleep(0.01)

    except Exception as e:
        print(f"--- ❌ ERROR IN STREAM ---: {e}")
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    finally:
        print("--- 🏁 TOKEN STREAM FINISHED ---")


@app.post("/conversation")
async def start_conversation(
    conv: ConversationStart,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    if conv.turns < 1 or conv.turns > 20:
        raise HTTPException(status_code=400, detail="Turns must be between 1 and 20")
    return StreamingResponse(
        conversation_generator(conv, request), media_type="text/event-stream"
    )


@app.get("/messages")
def get_messages(current_user: dict = Depends(get_current_user)):
    return {"messages": messages}


@app.get("/me")
def get_current_user_from_session(current_user: dict = Depends(get_current_user)):
    return current_user


@app.get("/")
def read_root():
    return {"message": "Chatbot API is running"}


def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()


@app.get("/get_prompts", response_model=list[schemas.Prompt])
async def get_prompts(
    user: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    prompts = db.scalars(
        select(models.Prompt)
        .where(models.Prompt.user == user)
        .order_by(models.Prompt.created_at.desc())
    ).all()

    return prompts


@app.post("/save_prompt", response_model=schemas.Prompt)
async def save_prompt(
    data: schemas.SavePrompt,
    user: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    agent_name_exists = db.scalars(
        select(models.Prompt).where(
            models.Prompt.user == user, models.Prompt.agent_name == data.agent_name
        )
    ).first()

    if agent_name_exists:
        raise HTTPException(
            status_code=409,
            detail=f"Another agent already saved as '{data.agent_name}'",
        )

    prompt = models.Prompt(**data.model_dump(), user=user)
    db.add(prompt)
    db.commit()
    db.refresh(prompt)

    return prompt


@app.put("/update_prompt/{prompt_id}", response_model=schemas.Prompt)
async def update_prompt(
    prompt_id: int,
    data: schemas.SavePrompt,
    user: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    agent_name_exists = db.scalars(
        select(models.Prompt).where(
            models.Prompt.user == user,
            models.Prompt.agent_name == data.agent_name,
            models.Prompt.id != prompt_id,
        )
    ).first()

    if agent_name_exists:
        raise HTTPException(
            status_code=409,
            detail=f"Another agent already saved as '{data.agent_name}'",
        )

    updated_prompt = db.scalars(
        update(models.Prompt)
        .where(models.Prompt.user == user, models.Prompt.id == prompt_id)
        .values(**data.model_dump())
        .returning(models.Prompt)
    ).first()

    if not updated_prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
        )
    db.commit()

    return updated_prompt


@app.delete("/delete_prompt/{prompt_id}")
async def delete_prompt(
    prompt_id: int,
    user: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    prompt = db.scalars(
        select(models.Prompt).where(
            models.Prompt.user == user, models.Prompt.id == prompt_id
        )
    ).first()

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
        )

    db.delete(prompt)
    db.commit()

    return {"message": "Prompt deleted successfully"}


@app.get("/download-chat/{thread_id}")
def download_chat(thread_id: str, current_user: dict = Depends(get_current_user)):
    """Download bots conversation in .txt file format"""
    history_text_A = chatbot_a.get_conversation_history(thread_id)
    print(history_text_A)

    headers = {
        "Content-Disposition": f"attachment; filename=conversation_{thread_id}.txt"
    }

    return Response(content=history_text_A, media_type="text/plain", headers=headers)


@app.post("/conversations", response_model=schemas.ConversationSchema)
async def save_conversation(
    data: schemas.SaveConversation,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """Save a conversation with all its messages"""
    conversation = models.Conversation(
        user=user_id,
        conversation_starter=data.conversation_starter,
        thread_id=data.thread_id,
        model=data.model,
        system_prompt_a=data.system_prompt_a,
        system_prompt_b=data.system_prompt_b,
        turns=data.turns,
    )
    db.add(conversation)
    db.flush()

    for idx, msg in enumerate(data.messages):
        message = models.Message(
            conversation_id=conversation.id,
            chatbot=msg.get("chatbot", "unknown"),
            message=msg.get("message", ""),
            order=idx,
        )
        db.add(message)

    db.commit()
    db.refresh(conversation)

    return conversation


@app.get("/conversations", response_model=list[schemas.ConversationSchema])
async def get_conversations(
    user_id: str = Depends(get_user_id), db: Session = Depends(get_db)
):
    """Get all conversations for the current user"""
    conversations = (
        db.query(models.Conversation)
        .filter(models.Conversation.user == user_id)
        .order_by(models.Conversation.created_at.desc())
        .all()
    )
    return conversations


@app.get("/conversations/{conversation_id}", response_model=schemas.ConversationSchema)
async def get_conversation(
    conversation_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """Get a specific conversation with all messages"""
    conversation = (
        db.query(models.Conversation)
        .filter(
            models.Conversation.id == conversation_id,
            models.Conversation.user == user_id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """Delete a conversation"""
    conversation = (
        db.query(models.Conversation)
        .filter(
            models.Conversation.id == conversation_id,
            models.Conversation.user == user_id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.delete(conversation)
    db.commit()

    return {"message": "Conversation deleted successfully"}


@app.put("/conversations/{conversation_id}", response_model=schemas.ConversationSchema)
def update_conversation(
    conversation_id: int,
    data: schemas.SaveConversation,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """Update an existing conversation and replace its messages."""
    with db.begin():
        conversation = (
            db.query(models.Conversation)
            .filter(
                models.Conversation.id == conversation_id,
                models.Conversation.user == user_id,
            )
            .first()
        )

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        conversation.conversation_starter = data.conversation_starter
        conversation.thread_id = data.thread_id
        conversation.model = data.model
        conversation.system_prompt_a = data.system_prompt_a
        conversation.system_prompt_b = data.system_prompt_b
        conversation.turns = data.turns

        db.query(models.Message).filter(
            models.Message.conversation_id == conversation.id
        ).delete(synchronize_session=False)

        for idx, msg in enumerate(data.messages):
            message = models.Message(
                conversation_id=conversation.id,
                chatbot=msg.get("chatbot", "unknown"),
                message=msg.get("message", ""),
                order=idx,
            )
            db.add(message)

    db.refresh(conversation)

    return conversation

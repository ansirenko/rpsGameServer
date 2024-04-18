import json

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware

import crud
import models
import schemas
from database import SessionLocal, engine
from game import GameManager

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Список источников, для которых разрешены кросс-доменные запросы
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_nickname(db, nickname=user.nickname)
    if db_user:
        raise HTTPException(status_code=400, detail="Nickname already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/{user_id}", response_model=schemas.UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        return schemas.UserResponse(success=False, message="User not found")
    return schemas.UserResponse(
        success=True,
        user_id=db_user.user_id,
        nickname=db_user.nickname,
        message="User retrieved successfully"
    )


@app.get("/stats/{user_id}", response_model=schemas.UserStatsResponse)
async def get_user_stats(user_id: int, db: Session = Depends(get_db)):
    db_user_stats = crud.get_user_stats(db, user_id=user_id)
    if db_user_stats is None:
        raise HTTPException(status_code=404, detail="User stats not found")
    return db_user_stats


@app.post("/login/", response_model=schemas.UserResponse)
async def login(login_data: schemas.Login, db: Session = Depends(get_db)):
    user = crud.get_user_by_nickname(db, nickname=login_data.nickname)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not crud.check_password(login_data.password, user.password):
        raise HTTPException(status_code=403, detail="Incorrect password")

    return schemas.UserResponse(success=True, user_id=user.user_id, nickname=user.nickname, message="Login successful")


game_manager = GameManager()


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, db: Session = Depends(get_db)):
    await game_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)

            if data_json.get('action') == 'start_game':
                await game_manager.start_game(user_id, websocket, db)
            elif data_json.get('action') == 'cancel_search':
                await game_manager.cancel_search(user_id, websocket)
            elif data_json.get('action') == 'make_move':
                move = data_json.get('move')
                await game_manager.make_move(user_id, move, db)
            elif data_json.get('action') == 'timeout':
                await game_manager.timeout_game(user_id, db)
            elif data_json.get('action') == 'play_again':
                await game_manager.handle_play_again(user_id, db)
            elif data_json.get('action') == 'accepted_play_again':
                await game_manager.handle_play_again_response(user_id, db)
            elif data_json.get('action') == 'exit_game':
                await game_manager.exit_game(user_id, db)
            elif data_json.get('action') == 'logout':
                break
    except WebSocketDisconnect:
        await game_manager.disconnect(user_id)
    finally:
        await game_manager.disconnect(user_id)

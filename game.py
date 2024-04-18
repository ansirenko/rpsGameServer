import json
import time

from fastapi import WebSocket
from sqlalchemy.orm import Session

import crud
from models import GameSession, GameStat


class GameManager:
    def __init__(self):
        self.active_websockets = {}
        self.waiting_players = []
        self.play_again_requests = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_websockets[user_id] = websocket

    async def disconnect(self, user_id: str):
        if user_id in self.waiting_players:
            self.waiting_players.remove(user_id)
        websocket = self.active_websockets.pop(user_id, None)
        if websocket:
            try:
                await websocket.close()
            except RuntimeError as e:
                print(f"Error closing websocket for user {user_id}: {e}")

    async def start_game(self, user_id: str, websocket: WebSocket, db: Session):
        if not self.waiting_players:
            self.waiting_players.append(user_id)
        else:
            opponent_id = self.waiting_players.pop(0)

            new_game_session = GameSession(
                player1_id=user_id,
                player2_id=opponent_id,
                status='waiting'
            )
            db.add(new_game_session)
            db.commit()

            await self.active_websockets[opponent_id].send_text(
                json.dumps({"message": f"Game started with {user_id}", "session_id": new_game_session.session_id})
            )
            await websocket.send_text(
                json.dumps({"message": f"Game started with {opponent_id}", "session_id": new_game_session.session_id})
            )

    async def cancel_search(self, user_id: str, websocket: WebSocket):
        if user_id in self.waiting_players:
            self.waiting_players.remove(user_id)
        await websocket.send_text("Search cancelled")

    async def make_move(self, user_id: str, move: str, db: Session):

        print("IN MAKE MOVE user id: ", int(user_id), move)
        db.expire_all()
        db.expunge_all()

        current_session = db.query(GameSession).filter(
            (GameSession.player1_id == int(user_id)) | (GameSession.player2_id == int(user_id)),
            GameSession.status == 'waiting'
        ).order_by(GameSession.session_id.desc()).first()

        if current_session is None:
            await self.active_websockets[user_id].send_text(json.dumps({"error": "No active game session"}))
            return

        if str(current_session.player2_id) == user_id:
            current_session.player2_move = move
            db.commit()

        if str(current_session.player1_id) == user_id:
            current_session.player1_move = move
        else:
            current_session.player2_move = move
        db.commit()

        current_session = db.query(GameSession).filter(
            GameSession.session_id == current_session.session_id
        ).order_by(GameSession.session_id.desc()).first()

        if current_session is None:
            await self.active_websockets[user_id].send_text(json.dumps({"error": "No active game session"}))
            return

        if current_session.player1_move and current_session.player2_move:
            result = self.determine_winner(
                str(current_session.player1_id),
                current_session.player1_move,
                str(current_session.player2_id),
                current_session.player2_move)
            current_session.status = 'completed'
            db.commit()

            player1_stats = db.query(GameStat).filter_by(user_id=current_session.player1_id).first()
            player2_stats = db.query(GameStat).filter_by(user_id=current_session.player2_id).first()

            if player1_stats.last_game_session_id != current_session.session_id and player2_stats.last_game_session_id != current_session.session_id:
                if result['winner']:
                    winner_stats = player1_stats if result['winner'] == current_session.player1_id else player2_stats
                    loser_stats = player2_stats if result['winner'] == current_session.player1_id else player1_stats
                    winner_stats.wins += 1
                    loser_stats.losses += 1
                else:
                    player1_stats.draws += 1
                    player2_stats.draws += 1
                player1_stats.last_game_session_id = current_session.session_id
                player2_stats.last_game_session_id = current_session.session_id
                db.commit()

            await self.notify_players_result(str(current_session.player1_id), str(current_session.player2_id), result)

    async def timeout_game(self, user_id: str, db: Session):
        current_session = db.query(GameSession).filter(
            (GameSession.player1_id == user_id) | (GameSession.player2_id == user_id),
            GameSession.status == 'waiting'
        ).first()

        if current_session:
            current_session.status = 'timeout'
            db.commit()
            await self.notify_players_timeout(str(current_session.player1_id), str(current_session.player2_id), user_id)

    async def exit_game(self, user_id: str, db: Session):
        current_session = db.query(GameSession).filter(
            (GameSession.player1_id == user_id) | (GameSession.player2_id == user_id)
        ).order_by(GameSession.session_id.desc()).first()
        if current_session.status not in ['completed', 'timeout']:
            current_session.status = 'completed'
            db.commit()

        opponent_id = str(current_session.player1_id)
        if str(current_session.player1_id) == user_id:
            opponent_id = str(current_session.player2_id)
        if opponent_id in self.active_websockets:
            await self.active_websockets[opponent_id].send_text(json.dumps({
                "action": "game_over",
            }))

    async def notify_players_timeout(self, player1_id: str, player2_id: str, timed_out_user_id: str):
        timeout_message = json.dumps({
            "action": "timeout",
            "timed_out_user_id": timed_out_user_id
        })

        if player1_id in self.active_websockets:
            await self.active_websockets[player1_id].send_text(timeout_message)

        if player2_id in self.active_websockets:
            await self.active_websockets[player2_id].send_text(timeout_message)

    def play_again(self, user_id: str, opponent_id: str, db: Session):
        new_game_session = GameSession(
            player1_id=user_id,
            player2_id=opponent_id,
            status='waiting'
        )
        db.add(new_game_session)
        db.commit()

    async def handle_play_again(self, user_id: str, db: Session):
        last_game_session = db.query(GameSession).filter(
            (GameSession.player1_id == user_id) | (GameSession.player2_id == user_id),
            GameSession.status == 'completed'
        ).order_by(GameSession.session_id.desc()).first()

        if last_game_session:
            opponent_id = last_game_session.player2_id if last_game_session.player1_id == user_id else last_game_session.player1_id
            user = crud.get_user(db, user_id=int(user_id))

            self.play_again_requests[str(opponent_id)] = str(user_id)

            if str(opponent_id) in self.active_websockets:
                await self.active_websockets[str(opponent_id)].send_text(json.dumps({
                    "action": "play_again_request",
                    "data": user_id,
                    "user_info": user.nickname,
                }))

    async def handle_play_again_response(self, user_id: str, db: Session):
        opponent_id = self.play_again_requests.get(str(user_id))

        if opponent_id:
            await self.active_websockets[str(opponent_id)].send_text(json.dumps({
                "action": "play_again_accepted",
            }))
            self.play_again_requests.pop(str(user_id))
            self.play_again(user_id, opponent_id, db)

    def determine_winner(self, player1_id: str, player1_move: str, player2_id: str, player2_move: str):
        result = {}
        # Rules: 'rock' > 'scissors', 'scissors' > 'paper', 'paper' > 'rock'
        if player1_move == player2_move:
            result['winner'] = None
            result['result'] = "Draw"
        elif (player1_move == "rock" and player2_move == "scissors") or \
                (player1_move == "scissors" and player2_move == "paper") or \
                (player1_move == "paper" and player2_move == "rock"):
            result['winner'] = player1_id
            result['result'] = "Player 1 wins"
        else:
            result['winner'] = player2_id
            result['result'] = "Player 2 wins"
        return result

    async def notify_players_result(self, player1_id, player2_id, result):
        winner_id_str = str(result['winner']) if result['winner'] else "None"
        if winner_id_str == "None":
            player1_message = player2_message = "Draw"
        else:
            player1_message = "You won!" if winner_id_str == player1_id else "You lost"
            player2_message = "You won!" if winner_id_str == player2_id else "You lost"

        if str(player1_id) in self.active_websockets:
            print("notify_players_result notify result", player1_id)

            await self.active_websockets[str(player1_id)].send_text(json.dumps({
                "action": "game_result",
                "winner": winner_id_str,
                "result": player1_message
            }))
        if str(player2_id) in self.active_websockets:
            print("notify_players_result notify result", player2_id)
            await self.active_websockets[str(player2_id)].send_text(json.dumps({
                "action": "game_result",
                "winner": winner_id_str,
                "result": player2_message
            }))

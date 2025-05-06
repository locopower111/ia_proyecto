from flask import Flask, render_template, request, jsonify
import chess
import random

app = Flask(__name__)
board = chess.Board()

# Valores de piezas
piece_values = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0
}

def evaluate_board():
    """Evalúa la posición actual (positivo = ventaja blanca)"""
    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values[piece.piece_type]
            score += value if piece.color == chess.WHITE else -value
    return score

def get_best_move():
    """IA: Escoge mejor movimiento posible basado en evaluación básica"""
    best_move = None
    best_score = -float('inf') if board.turn == chess.WHITE else float('inf')

    for move in board.legal_moves:
        board.push(move)
        score = evaluate_board()
        board.pop()

        if board.turn == chess.BLACK and score > best_score:
            best_score = score
            best_move = move
        elif board.turn == chess.WHITE and score < best_score:
            best_score = score
            best_move = move

    return best_move if best_move else random.choice(list(board.legal_moves))

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/move", methods=["POST"])
def move():
    if board.is_game_over():
        result = board.result()
        return jsonify({
            "game_over": True,
            "result": result,
            "checkmate": board.is_checkmate(),
            "fen": board.fen()
        })

    # Movimiento del jugador
    move_uci = request.json.get("move")
    try:
        move = chess.Move.from_uci(move_uci)
        if move not in board.legal_moves:
            raise ValueError("Movimiento ilegal")
        board.push(move)
    except:
        return jsonify({"error": "Movimiento inválido"}), 400

    # Verificar si terminó el juego
    response_data = {
        "check": board.is_check(),
        "checkmate": board.is_checkmate(),
        "fen": board.fen()
    }

    if board.is_game_over():
        response_data.update({
            "game_over": True,
            "result": board.result()
        })
        return jsonify(response_data)

    # Movimiento de la IA
    ai_move = get_best_move()
    board.push(ai_move)

    response_data.update({
        "move": ai_move.uci(),
        "fen": board.fen(),
        "check": board.is_check(),
        "checkmate": board.is_checkmate(),
        "game_over": board.is_game_over(),
        "result": board.result() if board.is_game_over() else None
    })

    return jsonify(response_data)

@app.route("/reset", methods=["POST"])
def reset():
    global board
    board = chess.Board()
    return jsonify({
        "status": "reset",
        "fen": board.fen()
    })

if __name__ == "__main__":
    app.run(debug=True)

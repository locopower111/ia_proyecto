from flask import Flask, render_template, request, jsonify
import chess
import chess.polyglot
import random
import os

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

def get_opening_move(board):
    # Ruta del archivo actual (app.py)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Ruta al archivo de apertura relativa al script
    book_path = os.path.join(BASE_DIR, "book.bin")

    if not os.path.exists(book_path):
        print(f"[ERROR] Libro de aperturas no encontrado: {book_path}")
        return None
    try:
        
        with chess.polyglot.open_reader(book_path) as reader:
            entry = reader.weighted_choice(board)
            return entry.move
    except IndexError:
        # No hay jugada en el libro para esta posición
        return None

def evaluate_board():
    """Evalúa la posición actual (positivo = ventaja blanca)"""
    score = 0
    if board.is_checkmate():
        return float('inf') if board.turn == chess.BLACK else -float('inf')
    if board.is_stalemate():
        return 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values[piece.piece_type]
            score += value if piece.color == chess.WHITE else -value
    return score

def minimax_alphabeta(depth, alpha, beta, maximizing_player):
    """Algoritmo Minimax con poda alfa-beta"""
    if depth == 0 or board.is_game_over():
        return evaluate_board(), None

    best_move = None

    if maximizing_player:
        max_eval = -float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval, _ = minimax_alphabeta(depth - 1, alpha, beta, False)
            board.pop()

            if eval > max_eval:
                max_eval = eval
                best_move = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval, _ = minimax_alphabeta(depth - 1, alpha, beta, True)
            board.pop()

            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval, best_move

def get_best_move(depth=5):
    # Intentar jugar desde el libro
    opening_move = get_opening_move(board)
    if opening_move:
        return opening_move

    """Obtiene el mejor movimiento con Minimax y poda alfa-beta"""
    _, best_move = minimax_alphabeta(depth, -float('inf'), float('inf'), board.turn == chess.WHITE)
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

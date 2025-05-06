const board = Chessboard('board', {
    position: 'start',
    draggable: true,
    onDrop: handleMove
});

document.getElementById("reset").addEventListener("click", resetGame);

async function handleMove(source, target) {
    const move = source + target;
    const promotion = (move.length === 4 && move[1] === '7' && move[3] === '8') ? 'q' : '';
    const moveUCI = move + promotion;

    const response = await fetch("/move", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ move: moveUCI })
    });
    const data = await response.json();

    if (data.game_over) {
        document.getElementById("status").innerText = `Juego terminado: ${data.result}`;
        return;
    }

    board.move(data.move);
}

function resetGame() {
    fetch("/reset", { method: "POST" })  
        .then(() => {
            board.start();
            document.getElementById("status").innerText = "Juego en progreso...";
        });
}
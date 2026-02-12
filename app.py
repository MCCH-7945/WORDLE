#!/usr/bin/env python3
"""
Servidor para la interfaz web del solver WORDLE en español.
"""

from pathlib import Path

from flask import Flask, jsonify, render_template, request

# Importar el solver (nueva API basada en WordleSolver)
from wordle_solver import Patron, WordleSolver, cargar_palabras

app = Flask(__name__, template_folder="templates", static_folder="static")

# Cargar palabras al arrancar
PALABRAS = cargar_palabras(Path(__file__).parent / "palabras_es.txt")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/suggest", methods=["POST"])
def suggest():
    """
    Recibe historial de intentos: [ { "guess": "serio", "pattern": [0,1,2,0,0] }, ... ]
    pattern: 0 = gris, 1 = amarillo, 2 = verde
    Devuelve: { "count": N, "remaining": [...], "suggestions": [ {"word": "...", "info": float}, ... ] }
    """
    try:
        data = request.get_json() or {}
        history = data.get("history", [])
    except Exception:
        return jsonify({"error": "JSON inválido"}), 400

    # Construimos un solver nuevo por petición, usando toda la lista como universo
    solver = WordleSolver(PALABRAS)
    for item in history:
        guess = (item.get("guess") or "").lower().strip()
        pattern = item.get("pattern")
        if not guess or len(guess) != 5 or not guess.isalpha():
            return jsonify({"error": "Intento debe ser una palabra de 5 letras"}), 400
        if not pattern or len(pattern) != 5:
            return jsonify({"error": "Patrón debe tener 5 valores (0=gris, 1=amarillo, 2=verde)"}), 400
        try:
            patron_tup: Patron = tuple(int(p) for p in pattern)  # type: ignore[assignment]
        except (TypeError, ValueError):
            return jsonify({"error": "Patrón debe ser números 0, 1 o 2"}), 400
        if not all(p in (0, 1, 2) for p in patron_tup):
            return jsonify({"error": "Cada valor del patrón debe ser 0, 1 o 2"}), 400
        # Aplicar el feedback al solver (filtra internamente las restantes)
        solver.aplicar_feedback(guess, patron_tup)

    restantes = solver.restantes

    # Sugerencias (máximo 10)
    candidatos = restantes if len(restantes) <= 30 else PALABRAS
    mejores = solver.mejores_intentos(top_k=10, candidatos=candidatos, soluciones=restantes)
    suggestions = [{"word": w, "info": round(info, 2)} for w, info in mejores]

    return jsonify({
        "count": len(restantes),
        "remaining": restantes[:100],  # límite para no enviar miles
        "suggestions": suggestions,
    })


@app.route("/api/words")
def words_list():
    """Devuelve la lista de palabras (para referencia o búsqueda)."""
    return jsonify({"words": PALABRAS, "count": len(PALABRAS)})


if __name__ == "__main__":
    print(f"Palabras cargadas: {len(PALABRAS)}")
    print("Abre http://127.0.0.1:5000 en el navegador.")
    app.run(debug=True, port=5000)

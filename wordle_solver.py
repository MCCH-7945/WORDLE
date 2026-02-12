#!/usr/bin/env python3
"""
Solver de WORDLE en español usando teoría de la información (entropía, sorpresa).
Las palabras pueden tener letras repetidas (ej: CASA, PAPEL, BELLE).
Permite adivinar con cualquier palabra de 5 letras, incluido no-palabras.
"""

from __future__ import annotations

import math
from collections import Counter
from pathlib import Path
from typing import List, Optional, Tuple

# Patrón de feedback: 2 = verde, 1 = amarillo, 0 = gris (tupla de 5 ints)
Patron = Tuple[int, int, int, int, int]


def feedback_wordle(guess: str, target: str) -> Patron:
    """
    Calcula el patrón verde/amarillo/gris para una palabra intento y una solución.
    Soporta letras repetidas en ambas palabras.

    - Verde (2): la letra coincide en esa posición.
    - Amarillo (1): la letra está en la solución pero en otra posición (respetando
      cuántas veces aparece).
    - Gris (0): la letra no está o ya se "consumieron" todas las apariciones.
    """
    guess = guess.lower().strip()
    target = target.lower().strip()
    if len(guess) != 5 or len(target) != 5:
        raise ValueError("Guess y target deben tener 5 letras")

    # Primera pasada: marcar verdes y contar cuántas de cada letra quedan en target
    resultado: List[int] = [0, 0, 0, 0, 0]
    restante: Counter[str] = Counter()
    for i in range(5):
        if guess[i] == target[i]:
            resultado[i] = 2  # verde
        else:
            restante[target[i]] += 1

    # Segunda pasada: para posiciones no verdes, asignar amarillo o gris
    for i in range(5):
        if resultado[i] == 2:
            continue
        letra = guess[i]
        if restante[letra] > 0:
            resultado[i] = 1  # amarillo
            restante[letra] -= 1
        else:
            resultado[i] = 0  # gris

    return tuple(resultado)


def filtrar_por_patron(palabras: List[str], guess: str, patron: Patron) -> List[str]:
    """Devuelve las palabras que son coherentes con el intento y el patrón."""
    return [p for p in palabras if feedback_wordle(guess, p) == patron]


def entropia(n: int) -> float:
    """Entropía en bits de un conjunto uniforme de n elementos: log2(n)."""
    if n <= 0:
        return 0.0
    return math.log2(n)


def entropia_esperada_despues(guess: str, soluciones: List[str]) -> float:
    """
    Entropía esperada del conjunto de soluciones después de usar `guess`.
    E[H] = sum_p P(patrón p) * H(soluciones | p)
    """
    n = len(soluciones)
    if n == 0:
        return 0.0

    # Particionar soluciones por el patrón que producirían con este guess
    grupos: dict[Patron, int] = {}
    for sol in soluciones:
        p = feedback_wordle(guess, sol)
        grupos[p] = grupos.get(p, 0) + 1

    # H_esperada = sum (n_p / N) * log2(n_p)
    h_esperada = 0.0
    for _, n_p in grupos.items():
        if n_p > 0:
            h_esperada += (n_p / n) * math.log2(n_p)
    return h_esperada


def ganancia_informacion(
    guess: str, soluciones: List[str]
) -> float:
    """
    Ganancia de información (en bits) al usar `guess`.
    I = H(antes) - E[H(después)] = log2(N) - E[H(después)].
    """
    n = len(soluciones)
    if n <= 1:
        return 0.0
    h_antes = math.log2(n)
    h_despues = entropia_esperada_despues(guess, soluciones)
    return h_antes - h_despues


def sorpresa(patron: Patron, guess: str, soluciones: List[str]) -> float:
    """
    Sorpresa (en bits) al observar un patrón: -log2(P(patrón)).
    Cuanto más inesperado el patrón, más información aporta.
    """
    n = len(soluciones)
    if n == 0:
        return 0.0
    coherentes = filtrar_por_patron(soluciones, guess, patron)
    p = len(coherentes) / n
    if p <= 0:
        return float("inf")
    return -math.log2(p)


def mejores_intentos(
    soluciones: List[str],
    intentos_guess: Optional[List[str]] = None,
    top_k: int = 10,
) -> List[Tuple[str, float]]:
    """
    Ordena los intentos por ganancia de información esperada (mayor = mejor).
    Si intentos_guess es None, usa las propias soluciones como candidatos.
    """
    candidatos = intentos_guess if intentos_guess is not None else soluciones
    puntuaciones: List[Tuple[str, float]] = []
    for g in candidatos:
        if len(g) != 5 or not g.isalpha():
            continue
        g = g.lower()
        info = ganancia_informacion(g, soluciones)
        puntuaciones.append((g, info))
    puntuaciones.sort(key=lambda x: -x[1])
    return puntuaciones[:top_k]


def cargar_palabras(ruta: Optional[Path] = None) -> List[str]:
    """Carga palabras de 5 letras (una por línea)."""
    if ruta is None:
        ruta = Path(__file__).parent / "palabras_es.txt"
    if not ruta.exists():
        return []
    palabras = []
    for linea in ruta.read_text(encoding="utf-8").strip().splitlines():
        palabra = linea.split("#")[0].strip().lower()
        if len(palabra) == 5 and palabra.isalpha():
            palabras.append(palabra)
    return list(dict.fromkeys(palabras))  # sin duplicados, orden preservado


def jugar_interactivo(
    soluciones: List[str],
    intentos_guess: Optional[List[str]] = None,
) -> None:
    """
    Modo interactivo: el usuario introduce el intento y el patrón (v/a/g o 2/1/0)
    y el solver sugiere el siguiente paso.
    """
    candidatos = intentos_guess if intentos_guess is not None else soluciones
    restantes = list(soluciones)
    ronda = 1

    print("WORDLE Solver (español). Patrón: v=verde, a=amarillo, g=gris (o 2,1,0).")
    print("Introduce tu intento y el patrón, ej: casa vagag\n")

    while True:
        if not restantes:
            print("No quedan palabras coherentes con lo introducido.")
            break
        if len(restantes) == 1:
            print(f"La palabra es: {restantes[0].upper()}")
            break

        print(f"\n--- Ronda {ronda} ---")
        print(f"Palabras posibles: {len(restantes)}")
        mejores = mejores_intentos(restantes, candidatos, top_k=5)
        print("Mejores intentos (por información):")
        for palabra, info in mejores:
            print(f"  {palabra.upper():6}  ganancia ≈ {info:.2f} bits")

        entrada = input("Tu intento y patrón (o Enter para salir): ").strip()
        if not entrada:
            break

        partes = entrada.split()
        if len(partes) != 2 or len(partes[0]) != 5 or len(partes[1]) != 5:
            print("Formato: palabra de 5 letras + patrón de 5 caracteres (v/a/g o 2/1/0)")
            continue

        intento, patron_str = partes[0].lower(), partes[1].lower()
        # Convertir v/a/g o 2/1/0 a tupla
        mapeo = {"v": 2, "a": 1, "g": 0, "2": 2, "1": 1, "0": 0}
        try:
            patron = tuple(mapeo[c] for c in patron_str)
        except KeyError:
            print("Patrón: solo v, a, g (o 2, 1, 0)")
            continue

        restantes = filtrar_por_patron(restantes, intento, patron)
        ronda += 1


def simular(
    soluciones: List[str],
    palabra_secreta: str,
    max_intentos: int = 6,
) -> List[Tuple[str, Patron]]:
    """
    Simula una partida hasta acertar. Devuelve lista de (intento, patrón).
    Usa en cada paso el intento con mayor ganancia de información.
    """
    candidatos = list(soluciones)
    restantes = list(soluciones)
    historial: List[Tuple[str, Patron]] = []

    for _ in range(max_intentos):
        if not restantes:
            break
        # Si quedan pocas opciones, conviene adivinar solo entre ellas (para poder acertar)
        usar_como_guess = restantes if len(restantes) <= 30 else candidatos
        mejores = mejores_intentos(restantes, intentos_guess=usar_como_guess, top_k=1)
        if not mejores:
            break
        intento = mejores[0][0]
        patron = feedback_wordle(intento, palabra_secreta)
        historial.append((intento, patron))
        if patron == (2, 2, 2, 2, 2):
            break
        restantes = filtrar_por_patron(restantes, intento, patron)

    return historial


if __name__ == "__main__":
    import sys

    palabras = cargar_palabras()
    if not palabras:
        print("No se encontró palabras_es.txt. Crea un archivo con una palabra de 5 letras por línea.")
        sys.exit(1)

    print(f"Cargadas {len(palabras)} palabras de 5 letras (pueden tener letras repetidas).")

    if len(sys.argv) > 1 and sys.argv[1] == "sim":
        if len(sys.argv) < 3:
            print("Uso: python wordle_solver.py sim <palabra_secreta>")
            sys.exit(1)
        secreta = sys.argv[2].lower()
        if len(secreta) != 5 or not secreta.isalpha():
            print("La palabra secreta debe tener 5 letras.")
            sys.exit(1)
        if secreta not in palabras:
            print(f"'{secreta}' no está en la lista; se simula igual.")
        pasos = simular(palabras, secreta)
        for i, (intento, patron) in enumerate(pasos, 1):
            cadena = "".join("v" if x == 2 else "a" if x == 1 else "g" for x in patron)
            print(f"  {i}. {intento.upper()}  {cadena}")
        print(f"Resuelto en {len(pasos)} intentos.")
    else:
        jugar_interactivo(palabras)

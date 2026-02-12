#!/usr/bin/env python3
"""
Solver de WORDLE en español usando teoría de la información (entropía).
- Soporta letras repetidas (guess y target).
- Permite adivinar con cualquier palabra de 5 letras (incluido "no-palabras").
Mejoras implementadas:
1) Cache de feedback (lru_cache) para no recalcular patrones.
2) Patrón codificado como int base-3 (243 posibles) para contar con arreglos.
3) Cálculo de entropía esperada con counts[243] (sin dicts).
4) Separación ligera: motor (WordleSolver) + CLI (argparse).
"""

from __future__ import annotations

import argparse
import math
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

Patron = Tuple[int, int, int, int, int]
PATRONES_POSIBLES = 3**5  # 243


# ----------------------------
# Utilidades de patrón
# ----------------------------

def patron_a_int(p: Patron) -> int:
    """Codifica un patrón (0/1/2)^5 como int en base 3."""
    x = 0
    m = 1
    for d in p:
        x += d * m
        m *= 3
    return x


def int_a_patron(x: int) -> Patron:
    """Decodifica int base-3 a patrón de 5 dígitos (0/1/2)."""
    out = []
    for _ in range(5):
        out.append(x % 3)
        x //= 3
    return tuple(out)  # type: ignore[return-value]


def patron_str_a_patron(s: str) -> Patron:
    """Convierte 'vagag' o '21010' a Patron."""
    s = s.strip().lower()
    if len(s) != 5:
        raise ValueError("El patrón debe tener 5 caracteres.")
    mapeo = {"v": 2, "a": 1, "g": 0, "2": 2, "1": 1, "0": 0}
    try:
        return tuple(mapeo[c] for c in s)  # type: ignore[return-value]
    except KeyError as e:
        raise ValueError("Patrón inválido: usa solo v/a/g o 2/1/0.") from e


def patron_a_vag(p: Patron) -> str:
    return "".join("v" if d == 2 else "a" if d == 1 else "g" for d in p)


# ----------------------------
# Feedback Wordle (con repetidas)
# ----------------------------

def _feedback_wordle(guess: str, target: str) -> Patron:
    guess = guess.lower().strip()
    target = target.lower().strip()
    if len(guess) != 5 or len(target) != 5:
        raise ValueError("Guess y target deben tener 5 letras")

    resultado: List[int] = [0, 0, 0, 0, 0]
    restante: Counter[str] = Counter()

    # Verdes + conteo de lo que queda en target
    for i in range(5):
        if guess[i] == target[i]:
            resultado[i] = 2
        else:
            restante[target[i]] += 1

    # Amarillos/grises respetando multiplicidad
    for i in range(5):
        if resultado[i] == 2:
            continue
        letra = guess[i]
        if restante[letra] > 0:
            resultado[i] = 1
            restante[letra] -= 1
        else:
            resultado[i] = 0

    return tuple(resultado)  # type: ignore[return-value]


@lru_cache(maxsize=None)
def feedback_wordle(guess: str, target: str) -> Patron:
    """Versión cacheada."""
    return _feedback_wordle(guess, target)


@lru_cache(maxsize=None)
def feedback_wordle_int(guess: str, target: str) -> int:
    """Patrón cacheado ya codificado como int base-3."""
    return patron_a_int(_feedback_wordle(guess, target))


# ----------------------------
# Carga de palabras
# ----------------------------

def cargar_palabras(ruta: Optional[Path] = None) -> List[str]:
    """Carga palabras de 5 letras (una por línea), ignora comentarios '# ...'."""
    if ruta is None:
        ruta = Path(__file__).parent / "palabras_es.txt"
    if not ruta.exists():
        return []

    palabras: List[str] = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        palabra = linea.split("#", 1)[0].strip().lower()
        if len(palabra) == 5 and palabra.isalpha():
            palabras.append(palabra)

    # sin duplicados, orden preservado
    return list(dict.fromkeys(palabras))


# ----------------------------
# Motor
# ----------------------------

class WordleSolver:
    def __init__(self, soluciones: Sequence[str], candidatos: Optional[Sequence[str]] = None) -> None:
        self.soluciones_all = list(soluciones)
        self.candidatos_all = list(candidatos) if candidatos is not None else list(soluciones)
        self.restantes = list(soluciones)

    @staticmethod
    def _limpiar_candidatos(cands: Iterable[str]) -> List[str]:
        out = []
        seen = set()
        for g in cands:
            g = g.strip().lower()
            if len(g) != 5 or not g.isalpha():
                continue
            if g not in seen:
                seen.add(g)
                out.append(g)
        return out

    def reset(self) -> None:
        self.restantes = list(self.soluciones_all)

    def aplicar_feedback(self, guess: str, patron: Patron) -> None:
        guess = guess.strip().lower()
        p_int = patron_a_int(patron)
        self.restantes = [sol for sol in self.restantes if feedback_wordle_int(guess, sol) == p_int]

    def counts_patrones(self, guess: str, soluciones: Sequence[str]) -> List[int]:
        """counts[p] = número de soluciones que producirían el patrón p (0..242)."""
        guess = guess.strip().lower()
        counts = [0] * PATRONES_POSIBLES
        for sol in soluciones:
            counts[feedback_wordle_int(guess, sol)] += 1
        return counts

    @staticmethod
    def entropia_esperada_desde_counts(counts: Sequence[int], n: int) -> float:
        """E[log2(n_p)] ponderado por n_p/N (equivalente a tu implementación original)."""
        if n <= 0:
            return 0.0
        acc = 0.0
        for c in counts:
            if c > 1:
                acc += c * math.log2(c)
        return acc / n

    def ganancia_informacion(self, guess: str, soluciones: Optional[Sequence[str]] = None) -> float:
        soluciones = self.restantes if soluciones is None else soluciones
        n = len(soluciones)
        if n <= 1:
            return 0.0
        h_antes = math.log2(n)
        counts = self.counts_patrones(guess, soluciones)
        h_despues = self.entropia_esperada_desde_counts(counts, n)
        return h_antes - h_despues

    def mejores_intentos(
        self,
        top_k: int = 10,
        candidatos: Optional[Sequence[str]] = None,
        soluciones: Optional[Sequence[str]] = None,
    ) -> List[Tuple[str, float]]:
        soluciones = self.restantes if soluciones is None else list(soluciones)
        candidatos = self.candidatos_all if candidatos is None else list(candidatos)

        candidatos_limpios = self._limpiar_candidatos(candidatos)
        puntuaciones: List[Tuple[str, float]] = []
        for g in candidatos_limpios:
            info = self.ganancia_informacion(g, soluciones)
            puntuaciones.append((g, info))

        puntuaciones.sort(key=lambda x: -x[1])
        return puntuaciones[:top_k]


# ----------------------------
# Modos de uso
# ----------------------------

def jugar_interactivo(soluciones: List[str], candidatos: Optional[List[str]] = None) -> None:
    solver = WordleSolver(soluciones, candidatos)
    ronda = 1

    print("WORDLE Solver (español). Patrón: v=verde, a=amarillo, g=gris (o 2,1,0).")
    print("Ejemplo: casa vagag\n")

    while True:
        if not solver.restantes:
            print("No quedan palabras coherentes con lo introducido.")
            break
        if len(solver.restantes) == 1:
            print(f"La palabra es: {solver.restantes[0].upper()}")
            break

        print(f"\n--- Ronda {ronda} ---")
        print(f"Palabras posibles: {len(solver.restantes)}")

        # Heurística: si quedan pocas, adivina dentro de ellas para maximizar prob. de acertar
        usar_guess = solver.restantes if len(solver.restantes) <= 30 else (candidatos or soluciones)

        mejores = solver.mejores_intentos(top_k=5, candidatos=usar_guess, soluciones=solver.restantes)
        print("Mejores intentos (por info):")
        for palabra, info in mejores:
            print(f"  {palabra.upper():6}  ganancia ≈ {info:.2f} bits")

        entrada = input("Tu intento y patrón (Enter para salir): ").strip()
        if not entrada:
            break

        partes = entrada.split()
        if len(partes) != 2:
            print("Formato: palabra + patrón (5 chars). Ej: casa vagag")
            continue

        intento = partes[0].strip().lower()
        patron_s = partes[1].strip().lower()

        if len(intento) != 5 or not intento.isalpha():
            print("El intento debe ser una palabra de 5 letras (solo letras).")
            continue

        try:
            patron = patron_str_a_patron(patron_s)
        except ValueError as e:
            print(e)
            continue

        solver.aplicar_feedback(intento, patron)
        ronda += 1


def simular(soluciones: List[str], secreta: str, max_intentos: int = 6) -> List[Tuple[str, Patron]]:
    solver = WordleSolver(soluciones)
    secreta = secreta.strip().lower()
    historial: List[Tuple[str, Patron]] = []

    for _ in range(max_intentos):
        if not solver.restantes:
            break

        usar_guess = solver.restantes if len(solver.restantes) <= 30 else solver.candidatos_all
        mejor = solver.mejores_intentos(top_k=1, candidatos=usar_guess)[0][0]
        p = feedback_wordle(mejor, secreta)
        historial.append((mejor, p))

        if p == (2, 2, 2, 2, 2):
            break
        solver.aplicar_feedback(mejor, p)

    return historial


# ----------------------------
# CLI
# ----------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Wordle solver ES (entropía / info).")
    parser.add_argument(
        "--words",
        type=Path,
        default=None,
        help="Ruta a palabras_es.txt (una palabra de 5 letras por línea).",
    )

    sub = parser.add_subparsers(dest="cmd", required=False)

    p_play = sub.add_parser("play", help="Modo interactivo (por defecto).")

    p_sim = sub.add_parser("sim", help="Simula una partida contra una palabra secreta.")
    p_sim.add_argument("secreta", type=str, help="Palabra secreta de 5 letras.")
    p_sim.add_argument("--max", type=int, default=6, help="Máximo de intentos (default 6).")

    args = parser.parse_args()

    palabras = cargar_palabras(args.words)
    if not palabras:
        print("No se encontró palabras_es.txt. Crea un archivo con una palabra de 5 letras por línea.")
        return 1

    print(f"Cargadas {len(palabras)} palabras de 5 letras (pueden tener repetidas).")

    if args.cmd == "sim":
        secreta = args.secreta.lower()
        if len(secreta) != 5 or not secreta.isalpha():
            print("La palabra secreta debe tener 5 letras (solo letras).")
            return 1
        if secreta not in palabras:
            print(f"Nota: '{secreta}' no está en la lista; se simula igual.")

        pasos = simular(palabras, secreta, max_intentos=args.max)
        for i, (intento, patron) in enumerate(pasos, 1):
            print(f"  {i}. {intento.upper()}  {patron_a_vag(patron)}")
        print(f"Resuelto en {len(pasos)} intentos.")
        return 0

    # default: play
    jugar_interactivo(palabras)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

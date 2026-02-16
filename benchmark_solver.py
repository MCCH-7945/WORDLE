#!/usr/bin/env python3
"""
Benchmark del solver WORDLE: simula N partidas con palabra secreta aleatoria
y reporta la media (y otras estadísticas) de intentos necesarios para acertar.
"""

import argparse
import random
import statistics
from pathlib import Path

from wordle_solver import cargar_palabras, simular


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Simula partidas aleatorias y reporta media de intentos del solver.",
    )
    parser.add_argument(
        "-n",
        "--partidas",
        type=int,
        default=100,
        help="Número de partidas a simular (default: 100).",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=6,
        help="Máximo de intentos por partida (default: 6).",
    )
    parser.add_argument(
        "--words",
        type=Path,
        default=None,
        help="Ruta a palabras_es.txt (default: junto al script).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Semilla para reproducibilidad (opcional).",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Solo imprimir la media y una línea de resumen.",
    )
    args = parser.parse_args()

    ruta = args.words or Path(__file__).parent / "palabras_es.txt"
    palabras = cargar_palabras(ruta)
    if not palabras:
        print("No se encontró palabras_es.txt o está vacío.")
        return 1

    if args.seed is not None:
        random.seed(args.seed)

    n = args.partidas
    max_intentos = args.max
    intentos_por_partida: list[int] = []
    resueltas = 0
    distribucion: dict[int, int] = {i: 0 for i in range(1, max_intentos + 1)}

    for _ in range(n):
        secreta = random.choice(palabras)
        historial = simular(palabras, secreta, max_intentos=max_intentos)
        num_intentos = len(historial)
        intentos_por_partida.append(num_intentos)

        if historial and historial[-1][1] == (2, 2, 2, 2, 2):
            resueltas += 1
        distribucion[num_intentos] = distribucion.get(num_intentos, 0) + 1

    media = statistics.mean(intentos_por_partida)
    pct_resueltas = 100.0 * resueltas / n

    if args.quiet:
        print(f"{media:.2f}")
        return 0

    print("--- Benchmark solver WORDLE (español) ---")
    print(f"Partidas simuladas: {n}")
    print(f"Palabras en diccionario: {len(palabras)}")
    print(f"Máximo intentos por partida: {max_intentos}")
    if args.seed is not None:
        print(f"Semilla: {args.seed}")
    print()
    print("Intentos para acertar:")
    print(f"  Media:   {media:.2f}")
    if n > 1:
        print(f"  Desv. estándar: {statistics.stdev(intentos_por_partida):.2f}")
    print(f"  Mínimo: {min(intentos_por_partida)}")
    print(f"  Máximo: {max(intentos_por_partida)}")
    print()
    print(f"Partidas resueltas (acierto en ≤{max_intentos}): {resueltas}/{n} ({pct_resueltas:.1f}%)")
    print()
    print("Distribución de intentos (incluye fallos en 6):")
    for k in range(1, max_intentos + 1):
        count = distribucion.get(k, 0)
        bar = "█" * (count * 40 // max(n, 1)) + "░" * (40 - (count * 40 // max(n, 1)))
        print(f"  {k} intentos: {count:4d}  {bar}")
    print("---")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# WORDLE — Solver en español

Solver de WORDLE en español usando teoría de la información (entropía, sorpresa). Las palabras pueden tener letras repetidas.

---

## Cómo probar el código (paso a paso)

### Requisitos

- **Python 3** (3.8 o superior).
- Terminal (o Cursor/VS Code integrado).

### 1. Entrar al proyecto

Abre una terminal y ve a la carpeta del repo:

```bash
cd /ruta/donde/está/WORDLE
```

(Si ya tienes el proyecto abierto en Cursor, la terminal suele abrirse ya en esa carpeta.)

### 2. (Opcional) Crear un entorno virtual

Recomendado para no mezclar dependencias con el resto del sistema:

```bash
python3 -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

Solo hace falta para la **interfaz web** (Flask). Para usar solo la línea de comandos puedes saltar este paso.

```bash
pip install -r requirements.txt
```

### 4. Probar por línea de comandos

**Opción A — Modo interactivo**  
Tú introduces cada intento y el patrón que te dio el WORDLE; el programa te dice cuántas palabras quedan y sugiere el siguiente intento.

```bash
python wordle_solver.py
```

- Te mostrará “Palabras posibles” y “Mejores intentos”.
- Cuando te pida *Tu intento y patrón*, escribe por ejemplo:  
  `serio vagag`  
  (palabra de 5 letras + espacio + 5 letras de patrón: **v** = verde, **a** = amarillo, **g** = gris).
- Repite hasta acertar o hasta que quieras salir (Enter vacío para salir).

**Opción B — Simular una partida**  
El programa “juega” solo hasta adivinar la palabra que le indiques:

```bash
python wordle_solver.py sim barra
```

(Sustituye `barra` por cualquier palabra de 5 letras; si está en `palabras_es.txt`, la encontrará.)

### 5. Probar la interfaz web

1. Arranca el servidor:

   ```bash
   python app.py
   ```

2. En el navegador abre: **http://127.0.0.1:5000**

3. En la página:
   - Escribe **una letra en cada una de las 5 casillas**.
   - **Haz clic en cada casilla** para cambiar el color: gris → amarillo → verde (y vuelve a gris).
   - Pulsa **«Añadir intento»** para enviar el intento.
   - Verás cuántas palabras quedan y las **sugerencias** para el siguiente intento.
   - **«Reiniciar»** borra el historial y empieza de cero.

4. Para parar el servidor: en la terminal donde corre `python app.py`, pulsa **Ctrl+C**.

---

## Benchmark (media de intentos)

Para medir el rendimiento del solver: simula muchas partidas con **palabra secreta aleatoria** (elegida de `palabras_es.txt`) y muestra la **media de intentos** necesarios para acertar, desviación típica, distribución, etc.

```bash
python benchmark_solver.py -n 100 --seed 123
```

- **`-n`** / **`--partidas`**: número de partidas a simular (default: 100).
- **`--max`**: máximo de intentos por partida (default: 6).
- **`--seed`**: semilla para reproducir los mismos sorteos.
- **`-q`** / **`--quiet`**: solo imprime la media (útil para scripts).

Ejemplo de salida: media de intentos, mín/máx, % resueltas y un histograma de intentos (1–6).

---

## Resumen rápido

| Qué quieres hacer        | Comando / acción |
|--------------------------|------------------|
| Jugar tú, con sugerencias en terminal | `python wordle_solver.py` |
| Ver al programa resolver solo        | `python wordle_solver.py sim &lt;palabra&gt;` |
| Usar la interfaz en el navegador     | `pip install -r requirements.txt` → `python app.py` → abrir http://127.0.0.1:5000 |
| Medir rendimiento (media de intentos) | `python benchmark_solver.py -n 100` |

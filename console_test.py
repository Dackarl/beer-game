"""Prueba el motor del Beer Game en consola, sin interfaz y sin ML.
Corre N rondas con una politica de pedido automatica y guarda los
resultados en un CSV para revisarlos despues."""
import csv

from game.game_state import GameState, ROLES
from game.policies import politica_ingenua


def run(n_rondas=20, politica=politica_ingenua, verbose=True):
    gs = GameState()

    for _ in range(n_rondas):
        demanda = gs.start_round()
        pedidos = {role: politica(role, demanda[role], gs.players[role]) for role in ROLES}
        registro = gs.complete_round(pedidos)

        if verbose:
            linea = f"Ronda {registro['ronda']:>2} | "
            linea += " | ".join(
                f"{role}: inv={registro[f'{role}_inventario']:>3} "
                f"back={registro[f'{role}_backlog']:>3} "
                f"costo={registro[f'{role}_costo']:>5.1f}"
                for role in ROLES
            )
            print(linea)

    print("\nCosto total acumulado por jugador:")
    for role in ROLES:
        print(f"  {role}: {gs.players[role].total_cost:.1f}")
    print(f"Costo total del juego: {gs.total_cost():.1f}")

    with open("resultados_ronda.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=gs.history[0].keys())
        writer.writeheader()
        writer.writerows(gs.history)
    print("\nDatos guardados en resultados_ronda.csv")


if __name__ == "__main__":
    run()

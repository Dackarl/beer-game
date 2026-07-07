"""Politicas de pedido automaticas, solo para probar el motor en consola
(sin humanos todavia). Cuando llegue Streamlit, estas se reemplazan por
la decision real que escriba cada jugador."""


def politica_ingenua(role, demanda_recibida, player):
    """Pide exactamente lo que acaba de recibir de demanda.
    Es la politica clasica que muestra el efecto bullwhip: cualquier
    variacion de demanda se amplifica rio arriba."""
    return demanda_recibida


def politica_nivel_objetivo(role, demanda_recibida, player, nivel_objetivo=12):
    """Pide lo necesario para volver a un inventario objetivo, cubriendo
    tambien el backlog pendiente. Es una politica mas estable/racional."""
    faltante = nivel_objetivo - player.inventory + player.backlog
    return max(0, faltante)

def _get_next_cell_state(grid: list[list[int]], r: int, c: int, rows: int, cols: int) -> int:
    """
    Calcula o próximo estado de uma célula com base nas regras do Game of Life.
    A grelha não é cíclica (fronteiras estritas).
    """
    live_neighbors = 0
    # Verificar as 8 posições adjacentes
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            #Validar se o vizinho está dentro dos limites da grelha
            if 0 <= nr < rows and 0 <= nc < cols:
                if grid[nr][nc] == 1:
                    live_neighbors += 1

    current_state = grid[r][c]

    #Aplicação das regras de Conway
    if current_state == 1:
        if live_neighbors < 2 or live_neighbors > 3:
            return 0 #Subpopulação ou Sobrepopulação
        return 1 #Mantém-se viva
    else:
        if live_neighbors == 3:
            return 1
        return 0


def game_of_life_sequencial (grid: list[list[int]], generations: int) -> list[list[int]]:
    """
    Simula a evolução da grelha durante um número fixo de gerações de forma sequencial.

    :param grid: Matriz bidimensional (lista de listas) com o estado inicial.
    :param generations: Número de gerações a simular.
    :return: A matriz final após todas as gerações.
    """

    if not grid or not grid[0]:
        return grid

    rows = len(grid)
    cols = len(grid[0])
    current_grid = [row[:] for row in grid] #Cópia profunda inicial

    for _ in range(generations):
        next_grid = [[0] * cols for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                next_grid[r][c] = _get_next_cell_state(current_grid, r, c, rows, cols)
        current_grid = next_grid

    return current_grid
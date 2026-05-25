import multiprocessing

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


def _worker_lifecycle( worker_id: int, shared_grid_flat, rows:int, cols:int, start_row: int, end_row: int, generations: int, barrier: multiprocessing):
    """
    Ciclo de vida de um worker. Cada worker foca-se na sua região de linhas,
    mas otimiza o cálculo focando-se apenas nas células que importam.
    """

    #Tamanho total para reconstruir a matriz localmente a cada iteração
    total_cells = rows*cols

    for gen in range(generations):
        # 1.Ler o estado atual da memória partilhada (Geração Atual)
        # Criamos uma representação local para leitura rápida

        local_grid = []
        for r in range(rows):
            start_idx = r*cols
            local_grid.append(list(shared_grid_flat[start_idx + cols]))

        # 2.Otimização Inteligente
        # Em vez de iterar cegamente por todas as células da região, vai descobrir quais as linhas da região têm células vivas por perto

        next_local_rows = {}

        # Analisamos apenas o bloco de linhas atribuído a este worker
        for r in range(start_row, end_row):
            # Verficiar se a linha atual, a de cima ou a de baixo têm alguma célula viva.
            # Se tudoá volta estiver morto, esta linha continuará morta e podemos saltá-la
            has_activity = False
            for check_r in (r-1, r, r+1):
                if 0 <= check_r < rows and any(local_grid[check_r]):
                    has_activity = True
                    break

            if has_activity:
                # Se houver atividade, calcula o novo estado para a linha inteira
                next_local_rows[r] = [0] * cols
                for c in range(cols):
                    next_local_rows[r][c] = _get_next_cell_state(local_grid, r, c, rows, cols)
            else:
                # Se não há atividade na vizinhança, a linha fica a 0
                next_local_rows[r] = [0] * cols

        # 3. Sincronizar antes de escrever
        # Garante que nenhum worker começa a desfigurar a mem´roa partilhada enquanto outros ainda estão a ler a geração atual
        barrier.wait()

        #4. Atualizar após escrever
        # Garamte que nenhum worker terminaram de escrever a nova geração antes de passar para a iteração seguinte
        for r in range(start_row, end_row):
            start_idc = r*cols
            shared_grid_flat[start_idx:start_idx+cols] = next_local_rows[r]

        # 5. Sincronizar antes de escrever
        # Garante que nenhum worker começa a desfigurar a mem´roa partilhada enquanto outros ainda estão a ler a geração atual
        barrier.wait()



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



import multiprocessing


def _get_next_cell_state(grid: list[list[int]], r: int, c: int, rows: int, cols: int) -> int:
    """Calcula o próximo estado de uma célula com base nas regras do Game of Life (não cíclico)."""
    live_neighbors = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if grid[nr][nc] == 1:
                    live_neighbors += 1

    current_state = grid[r][c]
    if current_state == 1:
        return 1 if live_neighbors in (2, 3) else 0
    else:
        return 1 if live_neighbors == 3 else 0


def _worker_lifecycle(worker_id: int, grid_a, grid_b, rows: int, cols: int,
                      start_row: int, end_row: int, generations: int, barrier: multiprocessing.Barrier):
    """
    Ciclo de vida do worker usando dupla paginação para evitar race conditions de leitura/escrita.
    """
    for gen in range(generations):
        # Determinar quem é o buffer de leitura e quem é o de escrita nesta geração
        if gen % 2 == 0:
            read_buffer = grid_a
            write_buffer = grid_b
        else:
            read_buffer = grid_b
            write_buffer = grid_a

        # Reconstruir a matriz local apenas para leitura estável
        local_grid = []
        for r in range(rows):
            start_idx = r * cols
            local_grid.append(list(read_buffer[start_idx: start_idx + cols]))

        # Otimização inteligente de atividade por vizinhança
        next_local_rows = {}
        for r in range(start_row, end_row):
            has_activity = False
            for check_r in (r - 1, r, r + 1):
                if 0 <= check_r < rows and any(local_grid[check_r]):
                    has_activity = True
                    break

            next_local_rows[r] = [0] * cols
            if has_activity:
                for c in range(cols):
                    next_local_rows[r][c] = _get_next_cell_state(local_grid, r, c, rows, cols)

        # Escrever os resultados diretamente no buffer de escrita dedicado
        for r in range(start_row, end_row):
            start_idx = r * cols
            write_buffer[start_idx: start_idx + cols] = next_local_rows[r]

        # Sincronização global: Todos os workers têm de fechar a geração 'gen'
        # antes que qualquer um possa saltar para a geração 'gen+1' e inverter os buffers
        barrier.wait()


def game_of_life_sequencial(grid: list[list[int]], generations: int) -> list[list[int]]:
    """Simula a evolução da grelha de forma sequencial."""
    if not grid or not grid[0]:
        return grid
    rows, cols = len(grid), len(grid[0])
    current_grid = [row[:] for row in grid]

    for _ in range(generations):
        next_grid = [[0] * cols for _ in range(rows)]
        for r in range(rows):
            for c in range(cols):
                next_grid[r][c] = _get_next_cell_state(current_grid, r, c, rows, cols)
        current_grid = next_grid
    return current_grid


def game_of_life_parallel(grid: list[list[int]], generations: int, workers: int) -> list[list[int]]:
    """Simula a evolução da grelha em paralelo com consistência garantida."""
    if not grid or not grid[0] or workers <= 0:
        return grid

    rows, cols = len(grid), len(grid[0])
    workers = min(workers, rows)

    lines_per_worker = rows // workers
    remainder = rows % workers

    # Criar dois buffers em memória partilhada (Dupla Paginação)
    flat_grid = [cell for row in grid for cell in row]
    grid_a = multiprocessing.Array('i', flat_grid)
    grid_b = multiprocessing.Array('i', [0] * (rows * cols))

    barrier = multiprocessing.Barrier(workers)
    processes = []
    current_start_row = 0

    for i in range(workers):
        extra_row = 1 if i < remainder else 0
        current_end_row = current_start_row + lines_per_worker + extra_row

        p = multiprocessing.Process(
            target=_worker_lifecycle,
            args=(i, grid_a, grid_b, rows, cols, current_start_row, current_end_row, generations, barrier)
        )
        processes.append(p)
        p.start()
        current_start_row = current_end_row

    for p in processes:
        p.join()

    # O resultado final estará no buffer 
    final_buffer = grid_b if generations % 2 != 0 else grid_a
    final_flat = list(final_buffer)

    return [final_flat[r * cols: (r + 1) * cols] for r in range(rows)]
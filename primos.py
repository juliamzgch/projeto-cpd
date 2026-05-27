import multiprocessing
import random
import time
import math

def is_prime(n):
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    divisor = 5
    while divisor * divisor <= n:
        if n % divisor == 0 or n % (divisor + 2) == 0:
            return False
        divisor += 6
    return True

############ SEQUENTIAL ############
def find_max_prime_sequential(timeout):
    start_time = time.time()
    max_prime = 2
    number = 3  # Continuous and systematic exploration
    while (time.time() - start_time) < timeout:
        if is_prime(number):
            max_prime = number
        number += 2  # Test only odd numbers
    return max_prime

############ PARALLEL ############

## --- Version 1: Random Adaptive Jumps ---
def _worker_v1(timeout, start_time, shared_best, lock):
    number = 3
    jump_limit = 100
    last_prime_time = time.time()

    while (time.time() - start_time) < timeout:
        if is_prime(number):
            if number > shared_best.value:
                with lock:
                    if number > shared_best.value:
                        shared_best.value = number
            last_prime_time = time.time()
            # Prime found? Increase jump limit (max 50,000 to prevent freezing)
            jump_limit = min(50_000, jump_limit * 2)

        stuck_time = time.time() - last_prime_time
        # If stuck for a while without finding primes, dynamically reduce jump sizes
        if stuck_time > 1.5:
            jump_limit = max(10, int(jump_limit * 0.5))
        elif stuck_time > 0.5:
            jump_limit = max(50, int(jump_limit * 0.8))

        # Jump ahead starting from the global shared best to ensure progression
        number = shared_best.value + random.randrange(2, jump_limit)
        if number % 2 == 0:
            number += 1

def find_max_prime_parallel_v1(timeout, workers):
    start_time = time.time()
    with multiprocessing.Manager() as manager:
        shared_best = manager.Value(int, 3)
        lock = multiprocessing.Lock()
        processes = []

        for _ in range(workers):
            p = multiprocessing.Process( target=_worker_v1, args=(timeout, start_time, shared_best, lock) )
            processes.append(p)
            p.start()

        # Strict timeout monitoring by the main process
        time_elapsed = time.time() - start_time
        remaining_time = max(0.0, timeout - time_elapsed)

        for p in processes:
            p.join(timeout=remaining_time)

        # Coordinated Termination: Force-stop any workers still running (When it gets here, the time allowed has passed)
        for p in processes:
            if p.is_alive():
                p.terminate()
                p.join()

        return shared_best.value

## --- Version 2: Interleaving ---
def _worker_interleaving(worker_id, workers, timeout, start_time, shared_best, lock):
    # Each worker starts at a staggered offset and jumps by (2 * num_workers)
    step = workers * 2
    number = 3 + (worker_id * 2)

    while (time.time() - start_time) < timeout:
        if is_prime(number):
            if number > shared_best.value:
                with lock:
                    if number > shared_best.value:
                        shared_best.value = number
        number += step

def find_max_prime_parallel_v2(timeout, workers):
    start_time = time.time()
    with multiprocessing.Manager() as manager:
        shared_best = manager.Value(int, 2)
        lock = multiprocessing.Lock()
        processes = []

        for i in range(workers):
            p = multiprocessing.Process( target=_worker_interleaving, args=(i, workers, timeout, start_time, shared_best, lock) )
            processes.append(p)
            p.start()

        # Strict timeout monitoring by the main process
        time_elapsed = time.time() - start_time
        remaining_time = max(0.0, timeout - time_elapsed)

        for p in processes:
            p.join(timeout=remaining_time)

        # Coordinated Termination (When it gets here, the time allowed has passed)
        for p in processes:
            if p.is_alive():
                p.terminate()
                p.join()

        return shared_best.value

## --- Version 3: Static Blocks (Chunks) ---
def _worker_chunks(timeout, start_time, chunk_queue, shared_best, lock):
    while (time.time() - start_time) < timeout:
        try:
            # Non-blocking pull so workers don't hang at the end
            chunk_start, chunk_end = chunk_queue.get(timeout=0.1)
        except:
            break

        # Skip the block if its upper bound is lower than the best known prime
        if chunk_end <= shared_best.value:
            continue

        current_start = max(chunk_start, shared_best.value + 1)
        if current_start % 2 == 0:
            current_start += 1

        ## Avoid even numbers
        for number in range(current_start, chunk_end, 2):
            if (time.time() - start_time) >= timeout:
                return
            if is_prime(number):
                if number > shared_best.value:
                    with lock:
                        if number > shared_best.value:
                            shared_best.value = number

def find_max_prime_parallel_v3(timeout, workers):
    start_time = time.time()
    chunk_size = workers * 100_000
    chunk_queue = multiprocessing.Queue()

    # Pre-fill the queue with enough initial blocks
    current_base = 3
    for _ in range(2000*timeout):
        chunk_queue.put((current_base, current_base + chunk_size))
        current_base += chunk_size

    with multiprocessing.Manager() as manager:
        shared_best = manager.Value(int, 2)
        lock = multiprocessing.Lock()
        processes = []

        for _ in range(workers):
            p = multiprocessing.Process( target=_worker_chunks, args=(timeout, start_time, chunk_queue, shared_best, lock) )
            processes.append(p)
            p.start()

        # Strict timeout monitoring by the main process
        time_elapsed = time.time() - start_time
        remaining_time = max(0.0, timeout - time_elapsed)

        for p in processes:
            p.join(timeout=remaining_time)

        # Coordinated Termination
        for p in processes:
            if p.is_alive():
                p.terminate()
                p.join()

        return shared_best.value

## --- Version 4: Optimized Dynamic Chunks with Early Discard (Winner) ---
def _worker_chunks_optimized(timeout, start_time, chunk_queue, shared_best, lock):
    while (time.time() - start_time) < timeout:
        try:
            chunk_start, chunk_end = chunk_queue.get(timeout=0.1)
        except:
            continue

        if chunk_end <= shared_best.value:
            continue

        current_start = max(chunk_start, shared_best.value + 1)
        if current_start % 2 == 0:
            current_start += 1

        for number in range(current_start, chunk_end, 2):
            # OPTIMIZATION: Immediate block discard if another worker has found a higher prime
            if chunk_end <= shared_best.value:
                break

            if (time.time() - start_time) >= timeout:
                return

            if is_prime(number):
                if number > shared_best.value:
                    with lock:
                        if number > shared_best.value:
                            shared_best.value = number

def find_max_prime_parallel_v4(timeout, workers):
    start_time = time.time()
    chunk_queue = multiprocessing.Queue()
    chunk_size = workers * 10_000_000

    current_base = 3
    for _ in range(5000):
        chunk_queue.put((current_base, current_base + chunk_size))
        current_base += chunk_size

    with multiprocessing.Manager() as manager:
        shared_best = manager.Value(int, 2)
        lock = multiprocessing.Lock()
        processes = []

        for _ in range(workers):
            p = multiprocessing.Process( target=_worker_chunks_optimized, args=(timeout, start_time, chunk_queue, shared_best, lock) )
            processes.append(p)
            p.start()

        # High-precision dynamic queue feeder loop (0.01s sleep)
        while (time.time() - start_time) < timeout:
            if chunk_queue.qsize() < 500:
                for _ in range(1000):
                    chunk_queue.put((current_base, current_base + chunk_size))
                    current_base += chunk_size
            time.sleep(0.01)

        time_elapsed = time.time() - start_time
        remaining_time = max(0.0, timeout - time_elapsed)

        for p in processes:
            p.join(timeout=remaining_time)

        # Coordinated Termination
        for p in processes:
            if p.is_alive():
                p.terminate()
                p.join()

        return shared_best.value

## --- Version 5: Optimized Dynamic Chunks with Early Discard And Backwards ---
def _worker_chunks_optimized_backwards(timeout, start_time, chunk_queue, shared_best, lock):
    while (time.time() - start_time) < timeout:
        try:
            chunk_start, chunk_end = chunk_queue.get(timeout=0.1)
        except:
            continue

        if chunk_end <= shared_best.value:
            continue

        limit_lower = max(chunk_start, shared_best.value + 1)


        current_top = chunk_end
        if current_top % 2 == 0:
            current_top -= 1

        for number in range(current_top, limit_lower - 1, -2):
            # OPTIMIZATION: Immediate block discard if another worker has found a higher prime
            if chunk_end <= shared_best.value:
                break

            if (time.time() - start_time) >= timeout:
                return

            if is_prime(number):
                if number > shared_best.value:
                    with lock:
                        if number > shared_best.value:
                            shared_best.value = number
                break

def find_max_prime_parallel_v5(timeout, workers):
    start_time = time.time()
    chunk_queue = multiprocessing.Queue()
    chunk_size = workers * 10_000_000

    current_base = 3
    for _ in range(5000):
        chunk_queue.put((current_base, current_base + chunk_size))
        current_base += chunk_size

    with multiprocessing.Manager() as manager:
        shared_best = manager.Value(int, 2)
        lock = multiprocessing.Lock()
        processes = []

        for _ in range(workers):
            p = multiprocessing.Process( target=_worker_chunks_optimized_backwards, args=(timeout, start_time, chunk_queue, shared_best, lock) )
            processes.append(p)
            p.start()

        # High-precision dynamic queue feeder loop (0.01s sleep)
        while (time.time() - start_time) < timeout:
            if chunk_queue.qsize() < 500:
                for _ in range(1000):
                    chunk_queue.put((current_base, current_base + chunk_size))
                    current_base += chunk_size
            time.sleep(0.01)

        time_elapsed = time.time() - start_time
        remaining_time = max(0.0, timeout - time_elapsed)

        for p in processes:
            p.join(timeout=remaining_time)

        # Coordinated Termination
        for p in processes:
            if p.is_alive():
                p.terminate()
                p.join()

        return shared_best.value

############ TESTS & RESULTS ############
# def results_parallel(t, function, w):
#     print(f"\n{function.__name__} | Searching for parallel solution in {t}s...")
#     print(f"Using {w} workers")
#
#     start_bench = time.time()
#     parallel_sol = function(t, w)
#     end_bench = time.time()
#
#     num_digits_parallel = num_digits(parallel_sol)
#
#     print(f"{function.__name__} | Max Parallel Prime found in {t}s: {parallel_sol}")
#     print(f"{function.__name__} | Parallel solution with {num_digits_parallel} digits")
#     print(f"{function.__name__} | Real Time: {end_bench - start_bench:.4f} seconds")

def _num_digits(number):
    if number < 1:
        return 1
    return int(math.log10(number)) + 1

def _print_table_header():
    print("\n" + "=" * 85)
    # Define column widths: 30 chars for version, 22 for prime, 12 for digits, 15 for time
    print(f"{'Algorithm Version':<30} | {'Max Prime Found':<22} | {'Digits':<12} | {'Execution Time':<15}")
    print("-" * 85)


def _print_table_row(version_name, prime, execution_time):
    digits = _num_digits(prime)
    formatted_prime = f"{prime:,}".replace(",", " ")  # Adds space separator for thousands readability
    formatted_time = f"{execution_time:.4f}s"
    print(f"{version_name:<30} | {formatted_prime:<22} | {digits:<12} | {formatted_time:<15}")


if __name__ == "__main__":
    timeout_input = int(input("Define timeout time (in seconds): "))
    workers_input = int(input("Define num of workers: "))

    print(f"\n[Benchmarking] Running tests with Timeout: {timeout_input}s and Workers: {workers_input}...")

    # Store results dynamically to print the structured table at the very end
    results = []

    # 1. Run Sequential Baseline
    start = time.time()
    sol_seq = find_max_prime_sequential(timeout_input)
    results.append(("Sequential", sol_seq, time.time() - start))

    # 2. Run Parallel V1
    start = time.time()
    sol_v1 = find_max_prime_parallel_v1(timeout_input, workers_input)
    results.append(("Parallel V1 (Random Jumps)", sol_v1, time.time() - start))

    # 3. Run Parallel V2
    start = time.time()
    sol_v2 = find_max_prime_parallel_v2(timeout_input, workers_input)
    results.append(("Parallel V2 (Interleave)", sol_v2, time.time() - start))

    # 4. Run Parallel V3
    start = time.time()
    sol_v3 = find_max_prime_parallel_v3(timeout_input, workers_input)
    results.append(("Parallel V3 (Chunks)", sol_v3, time.time() - start))

    # 5. Run Parallel V4
    start = time.time()
    sol_v4 = find_max_prime_parallel_v4(timeout_input, workers_input)
    results.append(("Parallel V4 (Optimized Chunks)", sol_v4, time.time() - start))

    # 6. Run Parallel V5
    start = time.time()
    sol_v5 = find_max_prime_parallel_v5(timeout_input, workers_input)
    results.append(("Parallel V5 (Opt Chunks Reversed)", sol_v5, time.time() - start))

    # Print consolidated results in a clean table ASCII format
    _print_table_header()
    for row in results:
        _print_table_row(row[0], row[1], row[2])
    print("=" * 85 + "\n")

    #
    # if __name__ == "__main__":
    #     timeout = int(input("Define timeout time (in seconds): "))
    #     workers = int(input("Define num of workers: "))
    #
    #     results_parallel(timeout, find_max_prime_parallel_v1, workers)
    #     results_parallel(timeout, find_max_prime_parallel_v2, workers)
    #     results_parallel(timeout, find_max_prime_parallel_v3, workers)
    #     results_parallel(timeout, find_max_prime_parallel_v4, workers)
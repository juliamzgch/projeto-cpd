import random
import time
import math


def is_prime(n: int) -> bool:
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


def find_max_prime_sequential_v1(timeout:int):
    start = time.time()
    max_prime = 1
    number = 3

    while (time.time() - start) < timeout:
        if is_prime(number):
            max_prime = number

        # Testar apenas números ímpares pq os pares nunca vão ser primos
        number += random.randrange(2, 100_000_000)
        # Se for par testamos o número seguinte (ímpar)
        if number % 2 == 0:
            number += 1

        #print(f"Current max prime: {max_prime}")
    return max_prime

def find_max_prime_sequential_v2(timeout: int):

    start = time.time()

    max_prime = 3
    number = 3

    # adaptive jump range
    jump_limit = 100_000_000

    # timer since last prime found
    last_prime_time = time.time()

    while (time.time() - start) < timeout:

        if is_prime(number):

            max_prime = number

            #print(f"New max prime: {max_prime}")

            # reset timer
            last_prime_time = time.time()

            # increase exploration again
            jump_limit = 100_000_000

        # how long since a new prime?
        stuck_time = time.time() - last_prime_time

        # adaptive behavior
        if stuck_time > 5:
            jump_limit = 1_000

        elif stuck_time > 2:
            jump_limit = 10_000

        # random jump
        number += random.randrange(2, jump_limit)

        # keep odd
        if number % 2 == 0:
            number += 1

    return max_prime


def results_sequential(t, function):
    print(f"{function.__name__} | Searching for sequential solution in {t}s...")

    sequential_sol = function(t)
    num_digits_sequential = num_digits(sequential_sol)

    print(f"{function.__name__} | Max Sequential Prime found in {t}s: {sequential_sol}")
    print(f"{function.__name__} | Sequential solution with {num_digits_sequential} digits")


def num_digits(number):
    return int(math.log10(number)) + 1

if __name__ == "__main__":
    timeout = int(input("Define timeout time (in seconds): "))

    results_sequential(timeout, find_max_prime_sequential_v1)
    results_sequential(timeout, find_max_prime_sequential_v2)

















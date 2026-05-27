import time
import random
from game_of_life import game_of_life_sequencial, game_of_life_parallel, game_of_life_parallel_default

def gerar_grelha_aleatoria(linhas: int, colunas: int, probabilidade_viva: float = 0.3) -> list[list[int]]:
    """Gera uma grelha binária aleatória com a dimensão especificada"""
    return [[1 if random.random() < probabilidade_viva else 0 for _ in range(colunas)] for _ in range (linhas)]

def comparar_matrizes(m1: list[list[int]], m2: list[list[int]]) -> bool:
    """Verifica se duas matrizes são exatamente iguais"""
    if len(m1) != len(m2) or len(m1[0]) != len(m2[0]):
        return False
    for r in range(len(m1)):
        for c in range(len(m1[0])):
            if m1[r][c] != m2[r][c]:
                return False

        return True

def executar_testes_game_of_life():
    print("=" *60)
    print(" INICIANDO TESTES AUTOMATICOS: GAME OF LIFE ")
    print("=" *60)

    #Configurações do teste

    linhas, colunas = 200, 200
    geracoes = 25
    num_workers = 4

    print("[*] Configuração: Grelha {linhas}x{colunas} | Gerações: {geracoes} | Workers: {num_workers}\n")

    #Gerar cenário

    grelha_inicial = gerar_grelha_aleatoria(linhas, colunas, probabilidade_viva=0.25)

    #TESTAR

    # Sequencial
    print("[+] A executar versão sequencial...")
    inicio_seq = time.perf_counter()
    resultado_seq = game_of_life_sequencial(grelha_inicial, geracoes)
    tempo_seq = time.perf_counter() - inicio_seq
    print(f"    -> Tempo Sequencial: {tempo_seq:.4f} segundos")

    # Paralela DEFAULT
    print("[+] A executar versão paralela DEFAULT (Sem otimização)...")
    inicio_def = time.perf_counter()
    resultado_def = game_of_life_parallel_default(grelha_inicial, geracoes, num_workers)
    tempo_def = time.perf_counter() - inicio_def
    print(f"    -> Tempo Paralelo Default: {tempo_def:.4f} segundos")

    # Paralela OTIMIZADA
    print("[+] A executar versão paralela OTIMIZADA...")
    inicio_opt = time.perf_counter()
    resultado_opt = game_of_life_parallel(grelha_inicial, geracoes, num_workers)
    tempo_opt = time.perf_counter() - inicio_opt
    print(f"    -> Tempo Paralelo Otimizado: {tempo_opt:.4f} segundos")

    # Validação (Validar as duas contra a sequencial para garantir que estão certas)
    print("\n[-] Verificando consistência dos resultados...")
    if comparar_matrizes(resultado_seq, resultado_def) and comparar_matrizes(resultado_seq, resultado_opt):
        print(" SUCCESS: Todas as versões produziram exatamente o mesmo resultado!")
        print(f"    -> Speedup da versão Default: {tempo_seq / tempo_def:.2f}x")
        print(f"    -> Speedup da versão Otimizada: {tempo_seq / tempo_opt:.2f}x")
        ganho_extra = (tempo_def - tempo_opt) / tempo_def * 100
        print(f"    -> A tua otimização poupou {ganho_extra:.1f}% de tempo face à Default!")
    else:
        print(" FAILED: Há divergência nos resultados de alguma das matrizes.")

if __name__ == "__main__":
        executar_testes_game_of_life()
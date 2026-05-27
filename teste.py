import time
import random
from game_of_life import game_of_life_sequencial, game_of_life_parallel

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
    geracoes = 50
    num_workers = 4

    print("[*] Configuração: Grelha {linhas}x{colunas} | Gerações: {geracoes} | Workers: {num_workers}\n")

    #Gerar cenário

    grelha_inicial = gerar_grelha_aleatoria(linhas, colunas, probabilidade_viva=0.25)

    #Executar VERSÃO SEQUENCIAL

    print("[+] A executar versão sequencial...")
    inicio_seq = time.perf_counter()
    resultado_seq= game_of_life_sequencial(grelha_inicial, geracoes)
    fim_seq = time.perf_counter()
    tempo_seq = fim_seq - inicio_seq
    print(f"     -> Tempo Sequencial: {tempo_seq:.4f} segundos")

    #Executar Versão Paralela
    print("[+] A executar versão paralela...")
    inicio_par = time.perf_counter()
    resultado_par = game_of_life_parallel(grelha_inicial, geracoes, num_workers)
    fim_par = time.perf_counter()
    tempo_par = fim_par - inicio_par
    print(f"    -> Tempo Paralelo: {tempo_par:.4f} segundos")



    #Validações

    print("\n[-] Verificando consistencia de resultados...")
    if comparar_matrizes(resultado_seq, resultado_par):
        print("SUCESSO: Ambas as versões produziram o mesmo resultado")

        #Calcular speedup
        speedup = tempo_seq/tempo_par
        print(f"    -> Speedup Alcançado: {speedup:.2f} vezes mais rapido")
        if speedup > 1.0:
            print("    -> Otimização bem-sucedida: A versão paralela foi mais rápida.")
        else:
            print(
                "    -> Nota: Para grelhas pequenas ou poucas gerações, o custo de criar processos pode não compensar.")
    else:
        print(" FAILED: Os resultados da versão sequencial e paralela são DIFERENTES.")
        print("           Verifica a gestão de fronteiras ou sincronização por barreiras.")

        print("=" * 60)

if __name__ == "__main__":
        executar_testes_game_of_life()
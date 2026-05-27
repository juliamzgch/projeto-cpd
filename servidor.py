
import socket
import json
import inspect
import threading
import time
import primos
import game_of_life

class Servidor:
    def __init__(self, host='localhost', port=80):
        self.host = host
        self.port = port
        self.funcs = {}
        self.running = True
        self.server_socket = None

        self._register_all_functions()

        self.clientes_ativos = 0
        self.lock = threading.Lock()
        self.shutdown_requested = False

    def _register_all_functions(self):
        modules = [primos, game_of_life]
        for module in modules:
            for name, func in inspect.getmembers(module, inspect.isfunction):
                if name.startswith('_'):
                    continue
                self.register(name, func)

    def register(self,name,func):
        self.funcs[name] = func
        print(f"[SERVIDOR] {name} registrado com sucesso!]")

    def list_methods_structured(self):
        funcoes = []
        for name, func in self.funcs.items():
            sig = inspect.signature(func)
            parametros = []
            for p in sig.parameters.values():
                if p.default != inspect.Parameter.empty:
                    parametros.append(f"{p.name}:{p.default!r}")
                else:
                    parametros.append(p.name)
            funcoes.append({
                "name": name,
                "args": parametros,
                "description": inspect.getdoc(func) or "",
            })
            return funcoes

    def handle_request(self, request_json):
        try:
            request = json.loads(request_json)

            method = request.get("method")
            args = request.get("params", {})
            req_id = request.get("id")

            if method == "list_methods":
                return json.dumps({
                    "jsonrpc": 2.0,
                    "result": self.list_methods_structured(),
                    "id": req_id
                })
            if method == "shutdown":
                print("[SERVIDOR] Encerramento solicitado.")
                self.shutdown_requested = True
                return json.dumps({
                    "jsonrpc": 2.0,
                    "result": "Encerrando...",
                    "id": req_id
                })
            func = self.funcs.get(method)
            if not func:
                return json.dumps({
                    "jsonrpc": 2.0,
                    "error": "Método não encontrado",
                    "id": req_id
                })

            if isinstance(args, dict) and '__args__' in args:
                real_args = args.pop('__args__')
                result = func(*real_args, **args)
            elif isinstance(args, dict):
                result = func(**args)
            elif isinstance(args, list):
                result = func(*args)
            else:
                result = func(args)

            return json.dumps({
                "jsonrpc": 2.0,
                "result": result,
                "id": req_id
            })

        except Exception as e:
            return json.dumps({
                "jsonrpc": 2.0,
                "error": str(e),
                "id": request.get("id") if 'request' in locals() else None
            })

    def client_thread(self, conn, addr):
        with self.lock:
            self.clientes_ativos += 1

        print(f"[SERVIDOR] Ligação de {addr}")

        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                request = data.decode()
                print(f"[SERVIDOR] {request}")
                response = self.handle_request(request)
                print(f"[SERVIDOR] {response}")
                conn.sendall(response.encode())

        with self.lock:
            self.clientes_ativos -= 1

        print(f"[SEERVIDOR] Cliente {addr} desligou.")

    def start(self):
        print(f"[SERVIDOR] Inicializando servidor...")
        print(f"[SERVIDOR] A escutar em {self.host}:{self.port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            s.settimeout(1)
            self.server_socket = s
            while not self.shutdown_requested:
                try:
                    conn, addr = s.accept()
                    threading.Thread(target=self.client_thread, args=(conn, addr)).start()
                except socket.timeout:
                    pass

        print(f"[SERVIDOR] Aguardando término dos clientes...")

        while True:
            with self.lock:
                if self.clientes_ativos == 0:
                    break
            time.sleep(0.5)
        print(f"[SERVIDOR] Todos os clientes desligaram. A encerrar.")

if __name__ == "__main__":
    server = Servidor()
    server.start()
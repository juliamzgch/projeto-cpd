
import socket
import json
import inspect
import threading
import time

import primos
import game_of_life

class Servidor:
    def __init__(self, host='localhost', port=8000):
        self.host = host
        self.port = port
        self.funcs = {}
        self.running = True
        self.server_socket = None

        self._register_all_functions()

        self.active_clients = 0
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
        functions = []
        for name, func in self.funcs.items():
            sig = inspect.signature(func)
            parametros = []
            for p in sig.parameters.values():
                if p.default != inspect.Parameter.empty:
                    parametros.append(f"{p.name}:{p.default!r}")
                else:
                    parametros.append(p.name)
            functions.append({
                "name": name,
                "args": parametros,
                "description": inspect.getdoc(func) or "",
            })
        return functions

    def handle_request(self, request_json):
        try:
            request = json.loads(request_json)

            method = request.get("method")
            args = request.get("params", {})
            req_id = request.get("id")

            if method == "list_methods":
                return json.dumps({
                    "jsonrpc": "2.0",
                    "result": self.list_methods_structured(),
                    "id": req_id
                })
            if method == "shutdown":
                print("[SERVIDOR] Shutdown requested.")
                self.shutdown_requested = True
                return json.dumps({
                    "jsonrpc": 2.0,
                    "result": "Shutting down...",
                    "id": req_id
                })
            func = self.funcs.get(method)
            if not func:
                return json.dumps({
                    "jsonrpc": 2.0,
                    "error": "Method Not Found",
                    "id": req_id
                })

            if isinstance(args, dict) and '__args__' in args:
                real_args = args.get('__args__', [])
                real_kwargs = {
                    k: v
                    for k, v in args.items()
                    if k != '__args__'
                }
                result = func(*real_args, **real_kwargs)
            elif isinstance(args, dict):
                result = func(**args)
            elif isinstance(args, list):
                result = func(*args)
            else:
                result = func(args)

            return json.dumps({
                "jsonrpc": "2.0",
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
            self.active_clients += 1

        print(f"[SERVER] Connection of {addr}")

        with conn:
            conn_file = conn.makefile("r")
            while True:
                request = conn_file.readline()
                if not request:
                    break
                print(f"[SERVER] {request}")
                response = self.handle_request(request)
                print(f"[SERVER] {response}")
                message = response + "\n"
                conn.sendall(message.encode())

        with self.lock:
            self.active_clients -= 1

        print(f"[SERVER] Client {addr} is off.")

    def start(self):
        print(f"[SERVER] Initializing server...")
        print(f"[SERVER] Listening on {self.host}:{self.port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
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

        print(f"[SERVER] Waiting for clients to finish...")

        while True:
            with self.lock:
                if self.active_clients == 0:
                    break
            time.sleep(0.5)
        print(f"[SERVER] All clients finished successfully.")
        print(f"[SERVER] Shutting down server...")

if __name__ == "__main__":
    server = Servidor()
    server.start()
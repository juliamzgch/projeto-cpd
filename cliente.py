import socket
import json
import ast

class Cliente:
    def __init__(self, host='localhost', port=8000):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.request_id = 0
        self.sock_file = self.sock.makefile("r")

    def invoke(self, function, arguments):
        if not self.sock:
            raise ConnectionError("Socket not connected.")

        self.request_id += 1

        request = {
            "jsonrpc": "2.0",
            "method": function,
            "params": arguments,
            "id": self.request_id
        }

        message = json.dumps(request) + "\n"

        self.sock.sendall(message.encode())

        response_line = self.sock_file.readline()
        response = json.loads(response_line)

        if isinstance(response, dict):
            if "result" in response:
                return response["result"]
            elif "error" in response:
                raise AttributeError(f"Remote error: {response['error']}")

        raise AttributeError("Resposta inválida do servidor.")

    def menu(self):
        while True:
            try:
                methods = self.invoke("list_methods", {})

            except Exception as e:
                print("Erro ao obter métodos: ", e)
                return

            print("\nMenu")

            for i, m in enumerate(methods):
                nome = m["name"]
                args = ", ".join(m["args"])
                desc = m["description"]
                print(f"{i + 1}. {nome}: {args} - {desc}")
            print("0. Sair")

            choice = input("Escolha: ").strip().lower()

            if choice == "0":
                print("A terminar cliente.")
                break
            if not choice.isdigit() or int(choice) < 0 or int(choice) > len(methods):
                print("Opção inválida.")
                continue

            method = methods[int(choice) - 1]
            func_name = method["name"]

            print(f"\nInvoke: {func_name}")
            params_input = input("Introduza argumentos: (ex: 1,2 ou x=1,y=2): ").strip()

            args = []
            kwargs = {}
            if params_input:
                parts = params_input.split(",")
                for part in parts:
                    if "=" in part:
                        k, v = part.split("=", 1)
                        try:
                            kwargs[k.strip()] = ast.literal_eval(v.strip())
                        except:
                            kwargs[k.strip()] = v.strip()
                    else:
                        try:
                            args.append(ast.literal_eval(part.strip()))
                        except:
                            args.append(part.strip())


                params = kwargs.copy()
                if args:
                    params["__args__"] = args

                try:
                    resultado = self.invoke(func_name, params)
                    print("Resultado: ", resultado)
                except Exception as e:
                    print("Erro: ", e)

    def __getattr__(self, name):
        def method(*args, **kwargs):
            if args and kwargs:
                return self.invoke(name, {"__args__": args, **kwargs})
            elif kwargs:
                return self.invoke(name, kwargs)
            else:
                return self.invoke(name, args)
        return method

if __name__ == "__main__":
    cliente = Cliente()
    cliente.menu()

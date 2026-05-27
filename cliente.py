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

    def invoke(self, function, arguments):
        if not self.sock:
            raise ConnectionError("Socket não está conectado.")

        self.request_id += 1

        request = {
            "jsonrpc": 2.0,
            "method": function,
            "params": arguments,
            "id": self.request_id
        }

        self.sock.sendall(json.dumps(request).encode())

        data = self.sock.recv(1024)
        response = json.loads(data.decode())

        if isinstance(response, dict):
            if "result" in response:
                return response["result"]
            elif "error" in response:
                raise AttributeError(f"Erro remoto: {response['error']}")

        raise AttributeError("Resposta inválida do servidor.")

    def menu(self):
        while True:
            try:
                metodos = self.invoke("list_methods", {})

            except Exception as e:
                print("Erro ao obter métodos: ", e)
                return

            print("\nMenu")

            for i, m in enumerate(metodos):
                nome = m["name"]
                args = ", ".join(m["args"])
                desc = m["description"]
                print(f"{i + 1}. {nome}: {args} - {desc}")
            print("0. Sair")

            escolha = input("Escolha: ").strip().lower()

            if escolha == "0":
                print("A terminar cliente.")
                break
            if not escolha.isdigit() or int(escolha) < 0 or int(escolha) > len(metodos):
                print("Opção inválida.")
                continue

            metodo = metodos[int(escolha) - 1]
            nome_funcao = metodo["name"]

            print(f"\nInvocar: {nome_funcao}")
            params_input = input("Introduza argumentos: (ex: 1,2 ou x=1,y=2): ").strip()

            args = []
            kwargs = {}
            if params_input:
                partes = params_input.split(",")
                for parte in partes:
                    parte = parte.split("=")
                    if "=" in parte:
                        k, v = parte.split("=", 1)
                        try:
                            kwargs[k.strip()] = ast.literal_eval(v.strip())
                        except:
                            kwargs[k.strip()] = v.strip()
                    else:
                        try:
                            args.append(ast.literal_eval(parte))
                        except:
                            args.append(parte)


                if kwargs:
                    params = kwargs.copy()
                    if args:
                        params["__args__"] = args
                    else:
                        params = args
                    try:
                        resultado = self.invoke(nome_funcao, params)
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

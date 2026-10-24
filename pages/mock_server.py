import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Tuple


class MockReqResHandler(BaseHTTPRequestHandler):
    """
    Servidor mock local que implementa fielmente os contratos da API ReqRes (/api/login),
    utilizado como fallback quando o limite diário de taxa pública da ReqRes (429) é atingido.
    Suporta simulação de rate limit (HTTP 429) para testes de retry.
    """

    # Contadores de nível de classe para simular comportamento entre requisições
    _request_count = 0
    _fail_first = False

    @classmethod
    def reset(cls):
        """Reseta os contadores de simulação do mock."""
        cls._request_count = 0
        cls._fail_first = False

    @classmethod
    def enable_fail_first(cls):
        """Habilita que a primeira requisição retorne HTTP 429 (rate limit)."""
        cls._request_count = 0
        cls._fail_first = True

    def do_POST(self):
        if self.path == "/api/login":
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
            try:
                data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
            except Exception:
                data = {}

            # Simulação de rate limit: primeira requisição retorna 429
            if MockReqResHandler._fail_first and MockReqResHandler._request_count == 0:
                MockReqResHandler._request_count += 1
                response_body = {"error": "Too many requests"}
                response_json = json.dumps(response_body).encode("utf-8")
                self.send_response(429)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(response_json)))
                self.end_headers()
                self.wfile.write(response_json)
                return

            MockReqResHandler._request_count += 1

            # Validação conforme contrato ReqRes
            if not data or ("email" not in data and "password" not in data):
                status = 400
                response_body = {"error": "Missing email or username"}
            elif "email" not in data:
                status = 400
                response_body = {"error": "Missing email or username"}
            elif "password" not in data:
                status = 400
                response_body = {"error": "Missing password"}
            elif data.get("email") == "eve.holt@reqres.in":
                status = 200
                response_body = {"token": "QpwL5tke4Pnpja7X4"}
            else:
                status = 400
                response_body = {"error": "user not found"}

            response_json = json.dumps(response_body).encode("utf-8")

            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response_json)))
            self.end_headers()
            self.wfile.write(response_json)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silencia logs no stdout para manter a saída do pytest limpa
        pass


def find_free_port() -> int:
    """Encontra uma porta TCP livre no sistema operacional."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def start_mock_server() -> Tuple[HTTPServer, str]:
    """
    Inicia o servidor mock em uma thread separada e retorna (server, base_url).
    """
    port = find_free_port()
    server = HTTPServer(("127.0.0.1", port), MockReqResHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    return server, base_url

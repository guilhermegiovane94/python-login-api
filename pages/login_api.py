import time
from typing import Any, Dict, Optional
import requests


class LoginApiResponse:
    """Wrapper para a resposta HTTP contendo métricas e métodos utilitários."""

    def __init__(self, raw_response: requests.Response, duration_ms: float):
        self.raw_response = raw_response
        self.status_code = raw_response.status_code
        self.duration = duration_ms
        self.headers = raw_response.headers

    def status(self) -> int:
        """Retorna o código de status HTTP (compatível com convenção Playwright/APIRequestContext)."""
        return self.status_code

    def json(self) -> Any:
        """Retorna o corpo da resposta em formato JSON."""
        return self.raw_response.json()

    @property
    def text(self) -> str:
        """Retorna o corpo da resposta em texto simples."""
        return self.raw_response.text

    @property
    def ok(self) -> bool:
        """Indica se a requisição foi bem-sucedida (status code 2xx)."""
        return self.raw_response.ok

    def __repr__(self) -> str:
        return f"<LoginApiResponse [{self.status_code}] duration={self.duration:.2f}ms>"


class LoginApi:
    """
    Camada de Serviço (Page Object / Service Object) para o endpoint de autenticação.
    Encapsula as requisições HTTP, lógica anti-flakiness (retry com backoff em 429) e validações.
    """

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        base_url: str = "https://reqres.in",
        max_retries: int = 3,
        retry_delay: float = 1.5,
    ):
        self.session = session or requests.Session()
        self.base_url = base_url.rstrip("/")
        self.endpoint = "/api/login"
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def sleep(self, seconds: float) -> None:
        """Aguarda um intervalo específico antes de uma nova tentativa."""
        time.sleep(seconds)

    def login(self, user_data: Dict[str, Any]) -> LoginApiResponse:
        """
        Envia uma requisição POST para o endpoint de login com política de retry automático.

        :param user_data: Dicionário contendo os dados do usuário (ex: email, password).
        :return: Objeto LoginApiResponse contendo a resposta e métricas.
        """
        url = f"{self.base_url}{self.endpoint}"
        last_response: Optional[LoginApiResponse] = None

        for attempt in range(1, self.max_retries + 1):
            start_time = time.perf_counter()
            response = self.session.post(url, json=user_data)
            duration_ms = (time.perf_counter() - start_time) * 1000

            api_response = LoginApiResponse(response, duration_ms)

            # Se não for rate limit (429), retorna a resposta imediatamente
            if api_response.status_code != 429:
                return api_response

            last_response = api_response

            # Se não for a última tentativa, aplica espera com backoff gradual
            if attempt < self.max_retries:
                self.sleep(self.retry_delay * attempt)

        return last_response if last_response is not None else api_response

    @staticmethod
    def validate_success_body(body: Dict[str, Any]) -> bool:
        """
        Valida se o corpo de resposta de sucesso contém um token válido.

        :param body: Dicionário retornado pela API.
        :return: True caso válido; lança ValueError caso inválido.
        """
        if not body or not isinstance(body.get("token"), str) or len(body.get("token", "")) == 0:
            raise ValueError("Corpo de resposta inválido: token não encontrado ou vazio.")
        return True

    @staticmethod
    def validate_error_body(body: Dict[str, Any]) -> bool:
        """
        Valida se o corpo de resposta de erro contém uma mensagem de erro válida.

        :param body: Dicionário retornado pela API.
        :return: True caso válido; lança ValueError caso inválido.
        """
        if not body or not isinstance(body.get("error"), str) or len(body.get("error", "")) == 0:
            raise ValueError("Corpo de resposta inválido: propriedade error não encontrada ou vazia.")
        return True

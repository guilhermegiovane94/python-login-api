import json
from pathlib import Path
import pytest
import requests
from pages.login_api import LoginApi
from pages.mock_server import start_mock_server

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_PATH = PROJECT_ROOT / "fixtures" / "users.json"


def pytest_addoption(parser):
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="Força o uso da API externa ao vivo (https://reqres.in), sem fallback para mock.",
    )
    parser.addoption(
        "--mock",
        action="store_true",
        default=False,
        help="Força o uso do mock server local.",
    )


@pytest.fixture(scope="session")
def users() -> dict:
    """Carrega as massas de teste a partir do arquivo JSON de fixtures."""
    with open(FIXTURES_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture(scope="session")
def session() -> requests.Session:
    """Fornece uma sessão HTTP reutilizável para a suíte de testes."""
    http_session = requests.Session()
    yield http_session
    http_session.close()


@pytest.fixture(scope="session")
def base_url(request) -> str:
    """
    Define a baseURL da aplicação.
    - Se --mock for fornecido: utiliza o mock server local.
    - Se --live for fornecido: utiliza https://reqres.in diretamente.
    - Modo padrão: testa https://reqres.in. Se responder com 429 (rate limit diário),
      ativa o mock server local automaticamente para evitar falsos negativos.
    """
    force_mock = request.config.getoption("--mock")
    force_live = request.config.getoption("--live")

    if force_mock:
        server, url = start_mock_server()
        yield url
        server.shutdown()
        return

    if force_live:
        yield "https://reqres.in"
        return

    # Verificação inteligente de disponibilidade da ReqRes
    try:
        check = requests.post(
            "https://reqres.in/api/login",
            json={"email": "eve.holt@reqres.in", "password": "cityslicka"},
            timeout=4,
        )
        if check.status_code != 429:
            yield "https://reqres.in"
            return
        else:
            print(
                "\n[AVISO] reqres.in retornou HTTP 429 (limite diário de 40 requisições do IP atingido)."
                "\n[AVISO] Ativando Mock Server local fiel aos contratos ReqRes para execução dos testes."
            )
    except Exception as e:
        print(f"\n[AVISO] Erro de conectividade com reqres.in: {e}. Utilizando Mock Server local.")

    server, url = start_mock_server()
    yield url
    server.shutdown()


@pytest.fixture(scope="function", autouse=True)
def reset_mock_counter():
    """Reseta o contador do mock server antes e depois de cada teste."""
    from pages.mock_server import MockReqResHandler

    MockReqResHandler.reset()
    yield
    MockReqResHandler.reset()


@pytest.fixture(scope="function")
def login_api(session: requests.Session, base_url: str) -> LoginApi:
    """Instancia a camada de serviço LoginApi com a baseURL resolvida."""
    return LoginApi(session=session, base_url=base_url)

import pytest
from pages.login_api import LoginApi


@pytest.mark.backend
class TestLoginApi:
    """Suíte de testes de backend para validação do endpoint /api/login (ReqRes)."""

    # ============================================================================
    # Cenário 1: Validação de endpoint e estrutura da resposta
    # ============================================================================
    def test_validacao_estrutura_resposta(self, login_api: LoginApi, users: dict):
        """
        Cenário 1: Deve retornar status 200, body com token, headers content-type JSON
        e tempo de resposta (duration) inferior a 30s para login válido.
        """
        response = login_api.login(users["validUser"])

        # Validação do código de status HTTP
        assert response.status() == 200, f"Esperado 200, obtido {response.status()}"
        assert response.status_code == 200

        # Validação do corpo da resposta (JSON)
        body = response.json()
        assert "token" in body, "Propriedade 'token' não encontrada no corpo da resposta"
        assert isinstance(body["token"], str), "Token deve ser uma string"
        assert len(body["token"]) > 0, "Token retornado não pode estar vazio"
        assert login_api.validate_success_body(body) is True

        # Validação de Headers
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type, f"Content-Type esperado application/json, obtido {content_type}"

        # Validação de SLA de Performance (duration em milissegundos)
        assert response.duration > 0, "Duração da requisição deve ser maior que 0ms"
        assert response.duration < 5000, f"Duração excedeu o SLA de 5s: {response.duration}ms"

    # ============================================================================
    # Cenário 2: Login com credenciais inválidas
    # ============================================================================
    def test_login_credenciais_invalidas(self, login_api: LoginApi, users: dict):
        """
        Cenário 2: Deve retornar status 400 e propriedade error informando 'user not found'.
        """
        response = login_api.login(users["invalidUser"])

        assert response.status_code == 400
        body = response.json()
        assert "error" in body
        assert isinstance(body["error"], str)
        assert len(body["error"]) > 0
        assert "user not found" in body["error"].lower()
        assert login_api.validate_error_body(body) is True

    # ============================================================================
    # Cenário 3: Validação de campos obrigatórios
    # ============================================================================
    def test_campo_password_obrigatorio(self, login_api: LoginApi, users: dict):
        """
        Cenário 3.1: Deve retornar erro 400 quando o campo password está ausente.
        """
        response = login_api.login(users["missingPassword"])

        assert response.status_code == 400
        body = response.json()
        assert "error" in body
        assert "password" in body["error"].lower()
        assert login_api.validate_error_body(body) is True

    def test_campo_email_obrigatorio(self, login_api: LoginApi, users: dict):
        """
        Cenário 3.2: Deve retornar erro 400 quando o campo email está ausente.
        """
        response = login_api.login(users["missingEmail"])

        assert response.status_code == 400
        body = response.json()
        assert "error" in body
        assert "email" in body["error"].lower()
        assert login_api.validate_error_body(body) is True

    def test_payload_vazio_obrigatorio(self, login_api: LoginApi, users: dict):
        """
        Cenário 3.3: Deve retornar erro 400 quando o body está vazio.
        """
        response = login_api.login(users["emptyBody"])

        assert response.status_code == 400
        body = response.json()
        assert "error" in body
        error_msg = body["error"].lower()
        assert "email" in error_msg or "username" in error_msg, \
            f"Esperado menção a email/username no erro, obtido: {body['error']}"
        assert login_api.validate_error_body(body) is True

    # ============================================================================
    # Cenário 4: Retry em rate limit (HTTP 429)
    # ============================================================================
    def test_retry_rate_limit_429(self, login_api: LoginApi, users: dict):
        """
        Cenário 4: Deve fazer retry automático quando a API retorna 429
        e retornar sucesso na segunda tentativa.
        """
        from pages.mock_server import MockReqResHandler

        MockReqResHandler.enable_fail_first()

        response = login_api.login(users["validUser"])

        assert response.status_code == 200, f"Esperado 200 após retry, obtido {response.status_code}"
        body = response.json()
        assert "token" in body
        assert isinstance(body["token"], str)
        assert len(body["token"]) > 0

    # ============================================================================
    # Cenário 5: Payload com tipos inválidos
    # ============================================================================
    def test_payload_tipos_invalidos(self, login_api: LoginApi, users: dict):
        """
        Cenário 5: Deve retornar erro quando o payload contém tipos inválidos
        (ex: email como número inteiro).
        """
        response = login_api.login({"email": 12345, "password": "senha123"})

        # O mock trata email não-cadastrado como "user not found"
        assert response.status_code == 400
        body = response.json()
        assert "error" in body
        assert isinstance(body["error"], str)
        assert len(body["error"]) > 0

    # ============================================================================
    # Cenário 6: Fluxo completo de validação backend (happy path + negative path)
    # ============================================================================
    def test_fluxo_completo_validacao_backend(self, login_api: LoginApi, users: dict):
        """
        Cenário 6: Deve validar happy path (sucesso) e negative path (falhas)
        em um único fluxo integrado sequencial de ponta a ponta.
        """
        # --- Happy Path: login com credenciais válidas ---
        success_response = login_api.login(users["validUser"])
        assert success_response.status_code == 200

        success_body = success_response.json()
        assert "token" in success_body
        assert isinstance(success_body["token"], str)
        assert len(success_body["token"]) > 0
        assert "application/json" in success_response.headers.get("content-type", "")

        # --- Negative Path: login com usuário não cadastrado ---
        invalid_response = login_api.login(users["invalidUser"])
        assert invalid_response.status_code == 400

        invalid_body = invalid_response.json()
        assert "error" in invalid_body
        assert "user not found" in invalid_body["error"].lower()

        # --- Negative Path: ausência do campo password ---
        missing_pass_response = login_api.login(users["missingPassword"])
        assert missing_pass_response.status_code == 400
        missing_pass_body = missing_pass_response.json()
        assert "error" in missing_pass_body
        assert "password" in missing_pass_body["error"].lower()

        # --- Negative Path: ausência do campo email ---
        missing_email_response = login_api.login(users["missingEmail"])
        assert missing_email_response.status_code == 400
        missing_email_body = missing_email_response.json()
        assert "error" in missing_email_body
        assert "email" in missing_email_body["error"].lower()

        # --- Negative Path: body vazio {} ---
        empty_body_response = login_api.login(users["emptyBody"])
        assert empty_body_response.status_code == 400
        empty_body_body = empty_body_response.json()
        assert "error" in empty_body_body

    # ============================================================================
    # Cenário 7: Validação direta dos métodos estáticos de validação de corpo
    # ============================================================================
    def test_validate_success_body_valido(self):
        """
        Cenário 7.1: validate_success_body deve retornar True para body válido.
        """
        assert LoginApi.validate_success_body({"token": "QpwL5tke4Pnpja7X4"}) is True

    def test_validate_success_body_invalido(self):
        """
        Cenário 7.2: validate_success_body deve lançar ValueError para body inválido.
        """
        with pytest.raises(ValueError):
            LoginApi.validate_success_body({})

        with pytest.raises(ValueError):
            LoginApi.validate_success_body({"token": ""})

        with pytest.raises(ValueError):
            LoginApi.validate_success_body({"token": 12345})

        with pytest.raises(ValueError):
            LoginApi.validate_success_body(None)

    def test_validate_error_body_valido(self):
        """
        Cenário 7.3: validate_error_body deve retornar True para body válido.
        """
        assert LoginApi.validate_error_body({"error": "user not found"}) is True

    def test_validate_error_body_invalido(self):
        """
        Cenário 7.4: validate_error_body deve lançar ValueError para body inválido.
        """
        with pytest.raises(ValueError):
            LoginApi.validate_error_body({})

        with pytest.raises(ValueError):
            LoginApi.validate_error_body({"error": ""})

        with pytest.raises(ValueError):
            LoginApi.validate_error_body({"error": 12345})

        with pytest.raises(ValueError):
            LoginApi.validate_error_body(None)

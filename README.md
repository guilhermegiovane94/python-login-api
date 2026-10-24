# 🔐 Projeto Python - Validação de Login (Backend Only)

Projeto de automação de testes de backend focado na validação de integridade, contratos e comportamento do endpoint de autenticação `/api/login` da API **ReqRes**, utilizando **Python**, **Pytest** e **Requests**, com padrão de projeto **Service Object**, massas desacopladas via **Fixtures JSON** e relatórios em HTML via **pytest-html**.

---

## ⚙️ Configurações do Projeto

### requirements.txt

```text
requests>=2.31.0
pytest>=8.0.0
pytest-html>=4.1.0
```

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v -s --strict-markers
markers =
    backend: Testes de API backend
```

---

## 🚀 Instalação no Windows

### Pré-requisitos

- **Python** 3.10 ou superior
- **pip** e **venv** habilitados

### Passo a Passo

1. Clone o repositório:

```powershell
git clone https://github.com/guilhermegiovane94/python-login-api.git
cd python-login-api
```

2. Crie e ative o ambiente virtual (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Instale as dependências:

```powershell
pip install -r requirements.txt
```

---

## 🧪 Executar Testes (Windows)

```powershell
# Todos os testes
pytest

# Com saída detalhada
pytest -v

# Gerar relatório HTML
pytest --html=reports/report.html --self-contained-html

# Forçar Mock Server local
pytest --mock

# Forçar API real (ReqRes)
pytest --live

# Executar teste específico por nome
pytest -k "credenciais_validas"
```

Para abrir o relatório HTML no navegador:

```powershell
start reports/report.html
```

---

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT**.

# ControleHoras3.0 — Floresta Jr.

Aplicação Flask para registrar entradas e saídas, acompanhar horas semanais e exportar relatórios Excel.

## Requisitos

- Python 3.10 ou superior
- Dependências listadas em `requirements.txt`

## Configuração local

1. Crie e ative um ambiente virtual.
2. Instale as dependências: `pip install -r requirements.txt`.
3. Defina variáveis de ambiente antes de iniciar o app. Nunca reutilize as senhas que já estiveram escritas no código.

Linux/macOS:
```bash
export FLASK_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
export ADMIN_PASSWORD="defina-uma-senha-forte"
python app.py
```

PowerShell:
```powershell
$env:FLASK_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
$env:ADMIN_PASSWORD = "defina-uma-senha-forte"
python app.py
```

A aplicação exige `FLASK_SECRET_KEY`; a senha administrativa é lida de `ADMIN_PASSWORD`. Não comite valores reais dessas variáveis. Em produção, use HTTPS e mantenha `COOKIE_SECURE` habilitado (padrão). Para desenvolvimento HTTP local, defina `COOKIE_SECURE=0`.

## PythonAnywhere

1. Faça checkout da branch de correção ou, depois de revisada, da versão aprovada.
2. No painel Web, configure `FLASK_SECRET_KEY` e `ADMIN_PASSWORD` no ambiente da aplicação/WSGI.
3. Confirme que `CONTROLE_HORAS_DB` aponta para o arquivo SQLite já usado pela instalação. Para evitar migração acidental, o padrão continua sendo `controle_horas.db` relativo ao diretório de trabalho do processo, como no código anterior. Se o WSGI executar com outro diretório de trabalho, defina `CONTROLE_HORAS_DB` com o caminho absoluto do banco existente **antes de recarregar**.
4. Instale as dependências no virtualenv associado ao site e recarregue a aplicação.
5. Se a exportação falhar, abra **Web → Log files → Error log** e verifique o traceback. A geração Excel agora ocorre em memória, sem exigir permissão para gravar arquivo de relatório na pasta do servidor.

Não substitua nem apague o banco existente durante a implantação. Faça uma cópia de segurança do arquivo SQLite antes de alterar configurações ou publicar uma versão nova.

## Comportamento e segurança

- Exportar gera um arquivo Excel em memória e não apaga registros.
- Limpar e excluir registros exigem sessão administrativa e requisição POST com token CSRF.
- Entradas duplicadas abertas são bloqueadas; a saída sem entrada aberta informa erro.
- Horas que atravessam a meia-noite são calculadas como jornada noturna.
- A distância do navegador é apenas informativa: como é enviada pelo cliente, não deve ser usada como prova de presença.
- Os segredos antigos que estiveram no código devem ser considerados expostos e substituídos por valores novos.

## Testes

Execute `python -m unittest discover -s tests -v`.

# Template API Python

## Requisitos
- Python instalado v3.9.X
- Instalar Pipenv:

```bash
pip install --user pipenv
```

## Configurar Banco de Dados
- Baixe o arquivo _**database.db**_ localizado dentro da pasta do desafio.
- Coloque esse arquivo dentro da raiz do projeto, ficando dessa forma:

```shell
src/
|-- server.py
database.db # coloque o arquivo aqui
...
```

## Rodar Projeto

Com o Python e o Pipenv instalado, rode o seguinte comando dentro da raiz do projeto para instalar as dependências.

```bash
pipenv install
```

Se caso ainda o intepretador do python não ache os módulos instalados rode o comando:

```bash
pipenv shell
```

Iniciar o projeto:

```bash
pipenv run python server.py
```

Agora sua API está rodando localmente em _**http://localhost:8080**_

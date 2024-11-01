# API de Gerenciamento de Produtos

Este projeto é uma API baseada em Flask para gerenciar produtos, relatórios de vendas e previsão de demanda. Ela interage com um banco de dados SQLite para fornecer funcionalidades de gerenciamento de produtos, relatórios de vendas e alertas de inventário.

## Funcionalidades

- Recuperar uma lista de produtos.
- Obter relatórios detalhados de vendas para um período especificado.
- Alertar sobre produtos próximos à data de validade.
- Prever a demanda de produtos com base em dados históricos de vendas.
- Servir páginas HTML para uma interface frontend amigável.

## Começando

### Pré-requisitos

Certifique-se de ter o Python instalado em sua máquina. Este projeto requer os seguintes pacotes Python:

- Flask
- pandas
- numpy
- scikit-learn
- sqlite3 (biblioteca padrão, nenhuma instalação necessária)

### Instalação

1. Clone o repositório ou baixe os arquivos do código.
2. Navegue até o diretório do projeto.
3. Instale os pacotes necessários:

   ```bash
   pip install Flask pandas numpy scikit-learn

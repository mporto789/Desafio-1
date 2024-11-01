import os
from datetime import datetime, timedelta
from sqlite3 import connect, Connection, Row

import numpy as np
import pandas as pd
from flask import Flask, jsonify, Response, request, send_from_directory
from sklearn.linear_model import LinearRegression

# Banco de Dados
DATABASE: str = "database.db"


def connection_database() -> Connection:
    """
    Cria, configura e retorna uma conexão com o Banco de Dados
    :return: Conexão com o Banco de Dados
    """
    connection: Connection = connect(DATABASE)
    connection.row_factory = Row
    return connection


# Rotas
server: Flask = Flask(__name__)


@server.get("/api/products")
def get_products():
    validity_date = request.args.get('validity_date')  # Obtém o parâmetro se existir
    database = connection_database()

    if validity_date:
        # Aqui você pode adicionar lógica para filtrar produtos pela data de validade
        query = "SELECT * FROM produto WHERE dataValidade = ?"
        cursor = database.execute(query, (validity_date,))
    else:
        query = "SELECT * FROM produto"
        cursor = database.execute(query)

    products = cursor.fetchall()
    return jsonify([dict(product) for product in products]), 200


@server.route("/products")
def products():
    """
    Serve a página de produtos.
    """
    return send_from_directory(frontend_dir, "products.html")



@server.get("/api/sales_report")
def get_sales_report() -> tuple[Response, int]:
    """
    Rota GET "/api/sales_report", para buscar relatório de vendas por período
    :return: Relatório detalhado de vendas para um período especificado
    """
    # Captura o parâmetro de dataValidade
    dataValidade = request.args.get("dataValidade") or request.args.get("datavalidade")
    # Captura o parâmetro de ordenação
    sort_by = request.args.get("sort_by", "quantidade_vendida")  # Padrão é 'quantidade_vendida'
    search_name = request.args.get("search_name", "")  # Nome do produto para pesquisa

    # Verifica se o parâmetro foi fornecido
    if not dataValidade:
        return jsonify({"error": "Parâmetro 'dataValidade' é obrigatório."}), 400

    # Validação de data
    try:
        dataValidade = datetime.strptime(dataValidade, "%d-%m-%Y")  # Altera o formato para DD-MM-AAAA
        if dataValidade > datetime.now():
            return jsonify({"error": "Data futura não permitida."}), 400
    except ValueError:
        return jsonify({"error": "Formato de data inválido, use DD-MM-AAAA."}), 400

    # Consulta ao banco de dados para o relatório
    database: Connection = connection_database()

    # Adiciona o filtro de pesquisa
    query = f"""
        SELECT p.nome AS nome_produto, p.estoqueAtual, 
               SUM(vp.quantidadeProduto) AS quantidade_vendida, 
               SUM(vp.quantidadeProduto * vp.precoVenda) AS total_vendas
        FROM produto p
        JOIN vendaProduto vp ON p.id = vp.produtoId
        JOIN venda v ON vp.vendaId = v.id
        WHERE v.dataVenda <= ? 
        AND p.nome LIKE ?  -- Filtro para o nome do produto
        GROUP BY p.id
        ORDER BY {sort_by} DESC  -- Ordena pela coluna especificada
    """

    cursor = database.execute(query, (dataValidade, f'%{search_name}%'))  # Pesquisa com LIKE
    sales_report = cursor.fetchall()

    return jsonify([dict(row) for row in sales_report]), 200


@server.route("/sales_report")
def sales_report():
    """
    Serve a página de vendas.
    """
    return send_from_directory(frontend_dir, "sales_report.html")  # Ajuste conforme o diretório correto

@server.get("/api/expiring_products_alert")
def expiring_products_alert() -> tuple[Response, int]:
    """
    Rota GET "/api/expiring_products_alert", que verifica e retorna produtos próximos à data de validade
    :return: Lista de produtos com validade próxima
    """
    alert_period = timedelta(days=7)
    today = datetime.now()
    target_date = (today + alert_period).strftime("%Y-%m-%d %H:%M:%S")

    database: Connection = connection_database()
    query = """
        SELECT nome, estoqueAtual, dataValidade
        FROM produto
        WHERE dataValidade <= ?
    """
    cursor = database.execute(query, (target_date,))
    expiring_products = cursor.fetchall()

    return jsonify([{
        "nome": product["nome"],
        "estoqueAtual": product["estoqueAtual"],
        "dataValidade": product["dataValidade"]
    } for product in expiring_products]), 200

@server.route("/expiring_products")
def expiring_products():
    """
    Serve o arquivo HTML para exibir produtos que estão próximos de expirar.
    """
    return send_from_directory(frontend_dir, "expiring_products.html")


@server.get("/api/demand_forecast")
def demand_forecast() -> tuple[Response, int]:
    """
    Rota GET "/api/demand_forecast", para previsão de demanda de produtos.
    :return: Lista de previsões de demanda para cada produto.
    """
    product_name = request.args.get('product_name')  # Obtém o nome do produto

    database: Connection = connection_database()
    query = """
        SELECT p.nome AS nome_produto, vp.produtoId, v.dataVenda, vp.quantidadeProduto 
        FROM venda v
        JOIN vendaProduto vp ON v.id = vp.vendaId
        JOIN produto p ON p.id = vp.produtoId
    """

    # Se um nome de produto for fornecido, filtramos a consulta
    if product_name:
        query += " WHERE p.nome LIKE ?"
        product_name = f"%{product_name}%"  # Usar LIKE para permitir busca parcial
    sales_data = pd.read_sql(query, database, params=(product_name,) if product_name else ())

    # Preprocessamento dos dados
    sales_data['dataVenda'] = pd.to_datetime(sales_data['dataVenda'])
    sales_data.set_index('dataVenda', inplace=True)
    product_forecasts = []

    for product_id, group in sales_data.groupby("produtoId"):
        # Somar as vendas diárias
        daily_sales = group['quantidadeProduto'].resample('D').sum().fillna(0)
        X = np.array(range(len(daily_sales))).reshape(-1, 1)
        y = daily_sales.values

        model = LinearRegression()
        model.fit(X, y)

        # Previsão para os próximos 30 dias
        future_days = np.array(range(len(daily_sales), len(daily_sales) + 30)).reshape(-1, 1)
        forecast = model.predict(future_days)

        product_forecasts.append({
            "product_id": group['nome_produto'].iloc[0],  # Obtemos o nome do produto
            "forecast": forecast.tolist()
        })

    return jsonify(product_forecasts), 200

@server.route("/demand_forecast")
def demand_forecast_page():
    """
    Serve a página de previsão de demanda.
    """
    return send_from_directory(frontend_dir, "demand_forecast.html")


# Diretório do frontend
frontend_dir = os.path.dirname(os.path.abspath(__file__))

@server.route("/")
def index():
    """
    Serve o arquivo HTML da interface frontend.
    """
    return send_from_directory(frontend_dir, "index.html")


if __name__ == "__main__":
    server.run(debug=True, port=3088)
from sqlite3 import connect, Connection, Row, Cursor
from flask import Flask, jsonify, Response, request
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
import numpy as np
import pandas as pd

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
def get_products() -> tuple[Response, int]:
    """
    Rota GET "/api/products", para buscar todos os produtos do Banco de Dados
    :return: Lista de Produtos cadastrados no Banco de Dados
    """
    database: Connection = connection_database()
    cursor: Cursor = database.execute("SELECT * FROM produto")

    products: list[any] = cursor.fetchall()

    return jsonify([dict(product) for product in products]), 200

@server.get("/api/sales_report")
def get_sales_report() -> tuple[Response, int]:
    print(f"Todos os parâmetros recebidos: {request.args}")
    """
    Rota GET "/api/sales_report", para buscar relatório de vendas por período
    :return: Relatório detalhado de vendas para um período especificado
    """
    # Captura o parâmetro de dataValidade
    dataValidade = request.args.get("dataValidade") or request.args.get("datavalidade")

    # Verifica se o parâmetro foi fornecido
    if not dataValidade:
        return jsonify({"error": "Parâmetro 'dataValidade' é obrigatório."}), 400

    # Validação de data
    try:
        dataValidade = datetime.strptime(dataValidade, "%Y-%m-%d")
        if dataValidade > datetime.now():
            return jsonify({"error": "Data futura não permitida."}), 400
    except ValueError:
        return jsonify({"error": "Formato de data inválido, use AAAA-MM-DD."}), 400

    # Consulta ao banco de dados para o relatório
    database: Connection = connection_database()
    query = """
        SELECT p.nome AS nome_produto, p.estoqueAtual, 
               SUM(vp.quantidadeProduto) AS quantidade_vendida, 
               SUM(vp.quantidadeProduto * vp.precoVenda) AS total_vendas
        FROM produto p
        JOIN vendaProduto vp ON p.id = vp.produtoId
        JOIN venda v ON vp.vendaId = v.id
        WHERE v.dataVenda <= ?  -- Usando apenas dataValidade
        GROUP BY p.id
        ORDER BY quantidade_vendida DESC
    """
    cursor = database.execute(query, (dataValidade,))
    sales_report = cursor.fetchall()

    return jsonify([dict(row) for row in sales_report]), 200


@server.get("/api/expiring_products_alert")
def expiring_products_alert() -> tuple[Response, int]:
    """
    Rota GET "/api/expiring_products_alert", que verifica e retorna produtos próximos à data de validade
    :return: Lista de produtos com validade próxima
    """
    alert_period = timedelta(days=7)
    today = datetime.now()
    database: Connection = connection_database()
    query = """
        SELECT nome, estoqueAtual, dataValidade
        FROM produto
        WHERE dataValidade <= ?
    """
    cursor = database.execute(query, (today + alert_period,))
    expiring_products = cursor.fetchall()

    return jsonify([{
        "nome": product["nome"],
        "estoqueAtual": product["estoqueAtual"],
        "dataValidade": product["dataValidade"]
    } for product in expiring_products]), 200


@server.get("/api/demand_forecast")
def demand_forecast() -> tuple[Response, int]:
    """
    Rota GET "/api/demand_forecast", para previsão de demanda de produtos
    :return: Lista de previsões de demanda para cada produto
    """
    database: Connection = connection_database()
    query = """
    SELECT vp.produtoId, v.dataVenda, vp.quantidadeProduto 
    FROM venda v
    JOIN vendaProduto vp ON v.id = vp.vendaId
    """
    sales_data = pd.read_sql(query, database)

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
            "product_id": product_id,
            "forecast": forecast.tolist()
        })

    return jsonify(product_forecasts), 200

if __name__ == "__main__":
    server.run(debug=True, port=3088)
import pandas as pd
from datetime import datetime

def calculate_metrics(data):
    """Calculate key metrics from the dataset."""
    total_multas = data['Auto de Infração'].nunique()
    valor_total_a_pagar = data[data['Status de Pagamento'] == 'NÃO PAGO']['Valor a Pagar (R$)'].sum()
    current_month = datetime.now().month
    current_year = datetime.now().year
    multas_mes_atual = data[(data['Data da Infração'].dt.month == current_month) &
                            (data['Data da Infração'].dt.year == current_year)]['Auto de Infração'].nunique()
    return total_multas, valor_total_a_pagar, multas_mes_atual

import pandas as pd

def load_data(file_path, sheet_name=None):
    """Load and preprocess the data."""
    try:
        # Detectar a aba automaticamente se não especificada
        sheet_name = sheet_name or 0

        # Carregar a planilha
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        # Padronizar os nomes das colunas
        column_mapping = {
            "Valor a ser pago R$": "Valor a ser pago R$",
            "Data da Infração": "Data da Infração",
            "Dia da Consulta": "Dia da Consulta",
            "Auto de Infração": "Auto de Infração",
        }
        df.rename(columns=column_mapping, inplace=True)

        # Verificar se as colunas essenciais existem
        required_columns = ['Dia da Consulta', 'Data da Infração', 'Valor a ser pago R$', 'Auto de Infração']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"As colunas essenciais estão ausentes: {', '.join([col for col in required_columns if col not in df.columns])}")

        # Converter colunas de datas para o formato datetime
        df['Dia da Consulta'] = pd.to_datetime(df['Dia da Consulta'], errors='coerce', dayfirst=True)
        df['Data da Infração'] = pd.to_datetime(df['Data da Infração'], errors='coerce', dayfirst=True)

        # Preprocessar o campo 'Valor a ser pago R$'
        df['Valor a ser pago R$'] = (
            df['Valor a ser pago R$']
            .astype(str)
            .str.replace(r'[^\d,.-]', '', regex=True)
            .str.replace(r'\.(?=\d{3,})', '', regex=True)
            .str.replace(',', '.')
            .apply(lambda x: float(x) if x.replace('.', '', 1).isdigit() else 0)
        )

        return df

    except Exception as e:
        print(f"Erro ao carregar os dados: {e}")
        raise

def clean_data(df):
    """Remove duplicates based on 'Auto de Infração'."""
    # Remove duplicados com base na coluna 'Auto de Infração'
    return df.drop_duplicates(subset=['Auto de Infração'])

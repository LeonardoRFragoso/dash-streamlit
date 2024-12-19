import pandas as pd


def load_data(file_path, sheet_name=None):
    """Load and preprocess the data."""
    try:
        # Detectar a aba automaticamente se não especificada
        sheet_name = sheet_name or 0

        # Carregar a planilha
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        # Padronizar os nomes das colunas (se forem inconsistentes)
        column_mapping = {
            "Valor a ser pago R$": "Valor a ser pago R$",
            "Data da Infração": "Data da Infração",
            "Dia da Consulta": "Dia da Consulta",
            "Auto de Infração": "Auto de Infração",
        }
        df.rename(columns=column_mapping, inplace=True)

        # Verificar se as colunas essenciais existem
        required_columns = ['Dia da Consulta', 'Data da Infração', 'Valor a ser pago R$', 'Auto de Infração']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"As colunas essenciais estão ausentes: {', '.join(missing_columns)}")

        # Converter colunas de datas para o formato datetime
        for date_col in ['Dia da Consulta', 'Data da Infração']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)

        # Preprocessar o campo 'Valor a ser pago R$'
        if 'Valor a ser pago R$' in df.columns:
            df['Valor a ser pago R$'] = (
                df['Valor a ser pago R$']
                .astype(str)
                .str.replace(r'[^\d,.-]', '', regex=True)  # Remove caracteres inválidos
                .str.replace(r'\.(?=\d{3,})', '', regex=True)  # Remove separadores de milhares
                .str.replace(',', '.', regex=False)  # Converte vírgula para ponto
            )
            # Converter para float
            df['Valor a ser pago R$'] = pd.to_numeric(df['Valor a ser pago R$'], errors='coerce').fillna(0)

        return df

    except Exception as e:
        print(f"Erro ao carregar os dados: {e}")
        raise


def clean_data(df):
    """Remove duplicates based on 'Auto de Infração'."""
    try:
        # Remove duplicados com base na coluna 'Auto de Infração'
        return df.drop_duplicates(subset=['Auto de Infração'], keep='last')
    except KeyError as e:
        raise ValueError(f"Erro ao limpar os dados: Coluna ausente {e}")
    except Exception as e:
        raise ValueError(f"Erro desconhecido ao limpar os dados: {e}")

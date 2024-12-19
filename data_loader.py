import pandas as pd


def load_data(file_path, sheet_name=None):
    """
    Carrega e processa os dados de um arquivo Excel.
    """
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
        verificar_colunas_essenciais(df, required_columns)

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

    except ValueError as e:
        raise RuntimeError(f"Erro de validação ao carregar os dados: {e}")
    except Exception as e:
        raise RuntimeError(f"Erro ao carregar os dados: {e}")


def clean_data(df):
    """
    Remove duplicados com base na coluna 'Auto de Infração'.
    """
    try:
        # Remove duplicados com base na coluna 'Auto de Infração'
        if 'Auto de Infração' not in df.columns:
            raise KeyError("'Auto de Infração' não encontrada no DataFrame.")
        return df.drop_duplicates(subset=['Auto de Infração'], keep='last')
    except KeyError as e:
        raise RuntimeError(f"Erro ao limpar os dados: {e}")
    except Exception as e:
        raise RuntimeError(f"Erro desconhecido ao limpar os dados: {e}")


def verificar_colunas_essenciais(df, required_columns):
    """
    Verifica a existência e o formato das colunas essenciais no DataFrame.
    """
    try:
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"As colunas essenciais estão ausentes: {', '.join(missing_columns)}")

        # Validar tipos das colunas essenciais
        if 'Valor a ser pago R$' in df and not pd.api.types.is_numeric_dtype(df['Valor a ser pago R$']):
            raise TypeError("A coluna 'Valor a ser pago R$' deve ser numérica.")
        for date_col in ['Dia da Consulta', 'Data da Infração']:
            if date_col in df and not pd.api.types.is_datetime64_any_dtype(df[date_col]):
                raise TypeError(f"A coluna '{date_col}' deve estar em formato datetime.")
    except Exception as e:
        raise RuntimeError(f"Erro na verificação de colunas essenciais: {e}")

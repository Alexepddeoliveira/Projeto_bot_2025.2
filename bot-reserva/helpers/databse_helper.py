import psycopg2
from config import DefaultConfig

def get_db_connection():
    """
    Cria e retorna uma nova conexão com o banco de dados.
    """
    try:
        conn = psycopg2.connect(DefaultConfig.DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

# Você pode adicionar mais funções aqui para fazer queries, etc.
# Por exemplo:
def fetch_some_data():
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        cur.execute("SELECT version();") # Query de exemplo
        data = cur.fetchone()
        cur.close()
        conn.close()
        return data
    return None
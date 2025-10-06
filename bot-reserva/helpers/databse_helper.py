import psycopg2
from config import DefaultConfig

def get_db_connection():
    """Cria e retorna uma nova conexão com o banco de dados."""
    try:
        conn = psycopg2.connect(DefaultConfig.DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def salvar_nova_reserva(reserva_data: dict):
    """
    Salva uma nova reserva no banco de dados.
    Não envia o ID, espera que o banco o gere.
    Retorna o ID da nova reserva em caso de sucesso.
    """
    # SQL modificado: removemos a coluna 'reserva_id' do insert.
    # Adicionamos "RETURNING reserva_id" para pegar o ID que o banco criou.
    sql = """
        INSERT INTO reservas (destino, hospedes, chegada, saida) 
        VALUES (%s, %s, %s, %s)
        RETURNING reserva_id; 
    """
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return None # Falha na conexão

        cur = conn.cursor()
        
        # Executa o comando SQL, sem o ID
        cur.execute(sql, (
            reserva_data['destino'],
            reserva_data['hospedes'],
            reserva_data['chegada'],
            reserva_data['saida']
        ))
        
        # Pega o ID que o banco retornou
        novo_id = cur.fetchone()[0]
        
        conn.commit()
        
        print(f"DEBUG: Reserva salva com sucesso! Novo ID do banco: {novo_id}")
        cur.close()
        return novo_id # Retorna o ID

    except Exception as e:
        print(f"!!!!!!!!!!!!!!! ERRO AO SALVAR RESERVA NO BANCO !!!!!!!!!!!!!!!")
        print(e)
        if conn:
            conn.rollback()
        return None # Retorna falha

    finally:
        if conn is not None:
            conn.close()
            
def buscar_reserva_por_id(reserva_id: int):
    """Busca uma reserva no banco de dados pelo seu ID."""
    sql = "SELECT * FROM reservas WHERE reserva_id = %s;"
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return None # Falha na conexão

        cur = conn.cursor()
        cur.execute(sql, (reserva_id,))
        reserva = cur.fetchone()
        cur.close()
        
        if reserva:
            reserva_dict = {
                'reserva_id': reserva[0],
                'destino': reserva[1],
                'hospedes': reserva[2],
                'chegada': reserva[3],
                'saida': reserva[4]
            }
            return reserva_dict
        else:
            return None

    except Exception as e:
        print(f"Erro ao buscar reserva no banco de dados: {e}")
        return None

    finally:
        if conn is not None:
            conn.close()
            
def atualizar_reserva(reserva_id: int, reserva_data: dict):
    """Atualiza uma reserva existente no banco de dados."""
    sql = """
        UPDATE reservas 
        SET destino = %s, hospedes = %s, chegada = %s, saida = %s 
        WHERE reserva_id = %s;
    """
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return False # Falha na conexão

        cur = conn.cursor()
        cur.execute(sql, (
            reserva_data['destino'],
            reserva_data['hospedes'],
            reserva_data['chegada'],
            reserva_data['saida'],
            reserva_id
        ))
        
        conn.commit()
        cur.close()
        
        return cur.rowcount > 0 # Retorna True se alguma linha foi atualizada

    except Exception as e:
        print(f"Erro ao atualizar reserva no banco de dados: {e}")
        if conn:
            conn.rollback()
        return False

    finally:
        if conn is not None:
            conn.close()
            
def deletar_reserva(reserva_id: int):
    """Deleta uma reserva do banco de dados pelo seu ID."""
    sql = "DELETE FROM reservas WHERE reserva_id = %s;"
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return False # Falha na conexão

        cur = conn.cursor()
        cur.execute(sql, (reserva_id,))
        
        conn.commit()
        cur.close()
        
        return cur.rowcount > 0 # Retorna True se alguma linha foi deletada

    except Exception as e:
        print(f"Erro ao deletar reserva no banco de dados: {e}")
        if conn:
            conn.rollback()
        return False

    finally:
        if conn is not None:
            conn.close()

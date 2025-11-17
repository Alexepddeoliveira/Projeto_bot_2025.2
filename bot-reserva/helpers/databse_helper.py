from azure.cosmos import CosmosClient, PartitionKey, exceptions
from config import DefaultConfig


# ===============================
# CONEXÃO COM O COSMOS DB (NoSQL)
# ===============================
# Esse módulo faz a ponte entre o bot e o banco.
# Agora ele fala com Azure Cosmos DB for NoSQL em vez de PostgreSQL.

# Cria o cliente principal do Cosmos
client = CosmosClient(
    DefaultConfig.COSMOS_ENDPOINT,
    credential=DefaultConfig.COSMOS_KEY,
)

# Garante que o database e o container existem
database = client.create_database_if_not_exists(id=DefaultConfig.COSMOS_DATABASE)
container = database.create_container_if_not_exists(
    id=DefaultConfig.COSMOS_CONTAINER,
    partition_key=PartitionKey(path="/id"),
    offer_throughput=400,  # ok pra demo/trabalho
)


def _get_next_reserva_id():
    """
    Descobre qual será o próximo número de reserva.
    Olha todas as reservas e pega o maior reserva_id, depois soma 1.
    Para trabalho de faculdade isso é suficiente.
    """
    query = "SELECT VALUE MAX(c.reserva_id) FROM c"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    current_max = items[0] if items and items[0] is not None else 0
    try:
        current_max = int(current_max)
    except (TypeError, ValueError):
        current_max = 0
    return current_max + 1


def salvar_nova_reserva(reserva_data: dict):
    """
    Salva uma nova reserva no Cosmos DB.
    Mantém a mesma ideia do código antigo:
    - recebe um dict com destino, hospedes, chegada, saida
    - retorna o ID da nova reserva em caso de sucesso
    """
    try:
        novo_id = _get_next_reserva_id()

        item = {
            "id": str(novo_id),          # ID obrigatório do Cosmos (string)
            "reserva_id": novo_id,      # ID numérico usado pelo resto do código
            "destino": reserva_data["destino"],
            "hospedes": reserva_data["hospedes"],
            "chegada": reserva_data["chegada"],
            "saida": reserva_data["saida"],
        }

        container.create_item(body=item)
        print(f"Reserva salva no Cosmos com ID {novo_id}")
        return novo_id

    except Exception as e:
        print("Erro ao salvar reserva no Cosmos:", e)
        return None


def buscar_reserva_por_id(reserva_id: int):
    """
    Busca uma reserva pelo número (reserva_id).
    Retorna um dicionário com os campos esperados ou None se não achar.
    """
    try:
        query = "SELECT * FROM c WHERE c.reserva_id = @id"
        params = [{"name": "@id", "value": int(reserva_id)}]

        items = list(
            container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True,
            )
        )

        if not items:
            return None

        item = items[0]

        return {
            "reserva_id": item.get("reserva_id"),
            "destino": item.get("destino"),
            "hospedes": item.get("hospedes"),
            "chegada": item.get("chegada"),
            "saida": item.get("saida"),
        }

    except Exception as e:
        print("Erro ao buscar reserva no Cosmos:", e)
        return None


def atualizar_reserva(reserva_id: int, reserva_data: dict):
    """
    Atualiza uma reserva existente.
    Retorna True se conseguiu atualizar, False caso contrário.
    """
    try:
        doc_id = str(reserva_id)
        pk = doc_id

        try:
            item = container.read_item(item=doc_id, partition_key=pk)
        except exceptions.CosmosResourceNotFoundError:
            return False

        item["destino"] = reserva_data["destino"]
        item["hospedes"] = reserva_data["hospedes"]
        item["chegada"] = reserva_data["chegada"]
        item["saida"] = reserva_data["saida"]

        container.replace_item(item=item, body=item)
        return True

    except Exception as e:
        print("Erro ao atualizar reserva no Cosmos:", e)
        return False


def deletar_reserva(reserva_id: int):
    """
    Deleta uma reserva pelo ID.
    Retorna True se conseguiu deletar, False caso contrário.
    """
    try:
        doc_id = str(reserva_id)
        pk = doc_id

        container.delete_item(item=doc_id, partition_key=pk)
        return True

    except exceptions.CosmosResourceNotFoundError:
        # Não achou a reserva
        return False

    except Exception as e:
        print("Erro ao deletar reserva no Cosmos:", e)
        return False

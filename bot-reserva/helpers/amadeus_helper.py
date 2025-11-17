import requests

AMADEUS_API_KEY = "pNOrXxSR5dCkPv3ABauNSjW5ssv3d9aP"
AMADEUS_API_SECRET = "oELWHTC9P6AMnAY1"

# Sandbox do Amadeus (ambiente de teste)
AMADEUS_BASE_URL = "https://test.api.amadeus.com"


def _get_access_token() -> str:
    """
    Pega um token de acesso no Amadeus usando client_credentials.
    """
    url = f"{AMADEUS_BASE_URL}/v1/security/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_API_KEY,
        "client_secret": AMADEUS_API_SECRET,
    }

    try:
        resp = requests.post(url, headers=headers, data=data)
        print("DEBUG TOKEN STATUS:", resp.status_code)
        print("DEBUG TOKEN BODY:", resp.text)
        resp.raise_for_status()
        body = resp.json()
        return body.get("access_token", "")
    except Exception as e:
        print("Erro ao obter token do Amadeus:", e)
        return ""


def consultar_voos_demo() -> str:
    """
    Consulta DEMO de voos no Amadeus.
    Usa valores fixos só para provar que integra (GRU -> GIG).
    """
    token = _get_access_token()
    if not token:
        return "Não consegui falar com a API de voos do Amadeus (token vazio)."

    url = f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers"
    params = {
        "originLocationCode": "GRU",       # São Paulo
        "destinationLocationCode": "GIG",  # Rio de Janeiro (Galeão)
        "departureDate": "2025-12-01",     # Data de exemplo
        "adults": "1",
        "max": "3",
    }
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.get(url, headers=headers, params=params)
        print("DEBUG FLIGHTS STATUS:", resp.status_code)
        print("DEBUG FLIGHTS BODY:", resp.text)
        resp.raise_for_status()
        data = resp.json()

        offers = data.get("data", [])
        if not offers:
            return "Amadeus respondeu, mas não encontrou voos para o exemplo."

        mensagens = ["Algumas opções de voo (Amadeus):"]
        for offer in offers[:3]:
            price = offer.get("price", {}).get("total", "???")
            itineraries = offer.get("itineraries", [])
            if not itineraries:
                continue
            first_segment = itineraries[0].get("segments", [])[0]
            carrier = first_segment.get("carrierCode", "??")
            departure = first_segment.get("departure", {}).get("at", "")
            arrival = first_segment.get("arrival", {}).get("at", "")
            mensagens.append(
                f"- Companhia {carrier}, saída {departure}, chegada {arrival}, preço total {price}"
            )

        return "\n".join(mensagens)

    except Exception as e:
        print("Erro ao consultar voos no Amadeus:", e)
        return "Deu erro ao tentar consultar voos no Amadeus."


def consultar_hoteis_demo() -> str:
    """
    Consulta DEMO de hotéis no Amadeus usando:
    /v1/reference-data/locations/hotels/by-city

    Lista alguns hotéis reais de RIO com nome, endereço e distância.
    Isso prova a integração com Amadeus para HOTÉIS.
    """
    token = _get_access_token()
    if not token:
        return "Não consegui falar com a API de hotéis do Amadeus (token vazio)."

    headers = {"Authorization": f"Bearer {token}"}

    # Busca hotéis pela cidade (RIO)
    url_ids = f"{AMADEUS_BASE_URL}/v1/reference-data/locations/hotels/by-city"
    params_ids = {
        "cityCode": "RIO",   # Rio de Janeiro
        "radius": 20,
        "radiusUnit": "KM",
        "hotelSource": "ALL",
    }

    try:
        resp_ids = requests.get(url_ids, headers=headers, params=params_ids)
        print("DEBUG HOTELS-IDS STATUS:", resp_ids.status_code)
        print("DEBUG HOTELS-IDS BODY:", resp_ids.text)
        resp_ids.raise_for_status()
        data_ids = resp_ids.json()

        hotels_list = data_ids.get("data", [])
        if not hotels_list:
            return "Amadeus respondeu, mas não retornou hotéis para RIO."

        mensagens = ["Alguns hotéis encontrados em RIO via Amadeus:"]

        # Pega até 5 hotéis só pra exemplo
        for h in hotels_list[:5]:
            nome = h.get("name", "Hotel sem nome")
            hotel_id = h.get("hotelId", "ID desconhecido")
            address = h.get("address", {})
            city = address.get("cityName", "Cidade desconhecida")
            lines = address.get("lines") or ["endereço não informado"]
            linha1 = lines[0]
            distance = h.get("distance", {})
            dist_val = distance.get("value")
            dist_unit = distance.get("unit", "KM")

            if dist_val is not None:
                mensagens.append(
                    f"- {nome} (ID: {hotel_id}) - {linha1}, {city} | Distância: {dist_val} {dist_unit}"
                )
            else:
                mensagens.append(
                    f"- {nome} (ID: {hotel_id}) - {linha1}, {city}"
                )

        return "\n".join(mensagens)

    except Exception as e:
        print("Erro ao consultar lista de hotéis no Amadeus:", e)
        return "Deu erro ao tentar consultar hotéis no Amadeus."

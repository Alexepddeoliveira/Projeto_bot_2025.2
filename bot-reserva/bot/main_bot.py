from botbuilder.core import ActivityHandler, TurnContext, MessageFactory, UserState, ConversationState
from botbuilder.schema import ChannelAccount
from botbuilder.dialogs import Dialog
from helpers.DialogHelper import DialogHelper

import requests

from helpers.amadeus_helper import consultar_voos_demo, consultar_hoteis_demo


# ============ CONFIGURAÇÃO DO AZURE LANGUAGE (CLU) ============

AZURE_LANGUAGE_ENDPOINT = "https://luisluis.cognitiveservices.azure.com/"
AZURE_LANGUAGE_KEY = "D3ufTnxYkBXC3jIspcSyrCiv5ciXIjWiqAg7nLlfQR98tlSSEucoJQQJ99BKACBsN54XJ3w3AAAaACOGRUig"
AZURE_PROJECT_NAME = "ReservaHotel"
AZURE_DEPLOYMENT_NAME = "production"


# Intents “oficiais” pro trabalho
INTENTS_VOO = {"ComprarVoo", "ConsultarVoo", "CancelarVoo"}
INTENTS_HOTEL = {"ReservarHotel", "ConsultarHotel", "CancelarHotel"}

# Mapa: nomes que vêm do Azure → nomes padronizados pro trabalho
INTENT_ALIAS_MAP = {
    # VOOS
    "ComprarPassagem": "ComprarVoo",
    "AlterarPassagem": "ConsultarVoo",
    "CacelarPassagem": "CancelarVoo",
    "CancelarPassagem": "CancelarVoo",

    # HOTÉIS
    "ReservarHotel": "ReservarHotel",
    "AlterarHotel": "ConsultarHotel",
    "CancelarHotel": "CancelarHotel",

    # Caso um dia existam direto
    "ConsultarVoo": "ConsultarVoo",
    "ConsultarHotel": "ConsultarHotel",
}


def pegar_intent_e_tokens_do_azure(texto: str):
    """
    Chama o Azure CLU e devolve:
      - intent bruta
      - lista de entidades (tokens) simples
    """
    if not texto:
        return "None", []

    url = f"{AZURE_LANGUAGE_ENDPOINT}/language/:analyze-conversations?api-version=2023-04-01"

    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_LANGUAGE_KEY,
        "Content-Type": "application/json",
    }

    body = {
        "kind": "Conversation",
        "analysisInput": {
            "conversationItem": {
                "id": "1",
                "participantId": "user",
                "text": texto,
            }
        },
        "parameters": {
            "projectName": AZURE_PROJECT_NAME,
            "deploymentName": AZURE_DEPLOYMENT_NAME,
            "verbose": True,
        },
    }

    try:
        resp = requests.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()

        prediction = data["result"]["prediction"]
        top_intent = prediction.get("topIntent", "None")
        entities = prediction.get("entities", [])

        print("DEBUG CLU prediction:", prediction)

        tokens = []
        for e in entities:
            tokens.append(
                {
                    "category": e.get("category"),
                    "text": e.get("text"),
                    "confidence": e.get("confidenceScore"),
                }
            )

        return top_intent, tokens

    except Exception as e:
        print("Erro chamando Azure Language:", e)
        return "None", []


def _resumir_tokens(tokens):
    """
    Pega as entidades do CLU e monta um resuminho amigável:
    cidade, data, número de pessoas, etc.
    """
    info = {}
    for t in tokens:
        cat = (t.get("category") or "").lower()
        txt = (t.get("text") or "").strip()
        if not txt:
            continue
        info[cat] = txt

    # procura por campos relevantes de forma “fuzzy”
    cidade = next((v for k, v in info.items() if "cidade" in k), None)
    data = next((v for k, v in info.items() if "data" in k), None)
    pessoas = next((v for k, v in info.items() if "pessoa" in k or "numero" in k), None)

    partes = []
    if cidade:
        partes.append(f"em {cidade}")
    if data:
        partes.append(f"na data {data}")
    if pessoas:
        partes.append(f"para {pessoas} pessoa(s)")

    if not partes:
        return ""

    return " " + ", ".join(partes)


def _descricao_acao(intent: str) -> str:
    """
    Traduz a intent "oficial" em uma frase amigável.
    """
    if intent == "ReservarHotel":
        return "reservar um hotel"
    if intent == "ConsultarHotel":
        return "consultar opções de hotel"
    if intent == "CancelarHotel":
        return "cancelar uma reserva de hotel"
    if intent == "ComprarVoo":
        return "comprar uma passagem de avião"
    if intent == "ConsultarVoo":
        return "consultar opções de voo"
    if intent == "CancelarVoo":
        return "cancelar uma passagem"
    return "te ajudar com sua viagem"


class MainBot(ActivityHandler):
    
    def __init__(
        self,
        dialog: Dialog,
        conversation_state: ConversationState,
        user_state: UserState,
    ):
        self.dialog = dialog
        self.conversation_state = conversation_state
        self.user_state = user_state

    async def on_turn(self, turn_context: TurnContext):
        await super().on_turn(turn_context)

        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    async def on_message_activity(self, turn_context: TurnContext):
        texto_usuario = turn_context.activity.text or ""

        # 1) CLU: intent + tokens
        intent_bruta, tokens = pegar_intent_e_tokens_do_azure(texto_usuario)
        intent = INTENT_ALIAS_MAP.get(intent_bruta, intent_bruta)

        print(f"DEBUG intent_bruta={intent_bruta} intent_mapeada={intent}")

        # 2) Monta frase amigável pro usuário
        resumo_tokens = _resumir_tokens(tokens)
        acao = _descricao_acao(intent)

        if intent in INTENTS_VOO or intent in INTENTS_HOTEL:
            msg_inicial = f"Beleza! Entendi que você quer {acao}{resumo_tokens}."
            await turn_context.send_activity(MessageFactory.text(msg_inicial))

        # 3) Integração com Amadeus + simulação de reserva

        if intent in INTENTS_VOO:
            await turn_context.send_activity(
                MessageFactory.text("Vou dar uma olhada nos voos disponíveis pra você 🚀...")
            )
            resultado_voos = consultar_voos_demo()
            await turn_context.send_activity(
                MessageFactory.text("Encontrei essas opções de voo:")
            )
            await turn_context.send_activity(MessageFactory.text(resultado_voos))
            await turn_context.send_activity(
                MessageFactory.text(
                    "Considere que escolhi a opção que melhor se encaixa pra você e "
                    "simulei a emissão da sua passagem. 😉\n"
                    "Se quiser registrar essa reserva no sistema interno, use o menu de *Novas Reservas* a seguir."
                )
            )

        elif intent in INTENTS_HOTEL:
            await turn_context.send_activity(
                MessageFactory.text("Vou buscar alguns hotéis legais pra você 🏨...")
            )
            resultado_hoteis = consultar_hoteis_demo()
            await turn_context.send_activity(
                MessageFactory.text("Olha algumas opções de hotel que encontrei:")
            )
            await turn_context.send_activity(MessageFactory.text(resultado_hoteis))
            await turn_context.send_activity(
                MessageFactory.text(
                    "Podemos considerar que a melhor opção acima foi reservada pra você, "
                    "com base nas informações que você informou. 💜\n"
                    "Se quiser armazenar essa reserva no sistema interno, é só usar o menu de *Novas Reservas*."
                )
            )

        else:
            # Não bateu em voo/hotel → cai pro fluxo normal dos diálogos
            await turn_context.send_activity(
                MessageFactory.text(
                    "Não entendi exatamente se é voo ou hotel, então vou te mostrar o menu de reservas 🙂"
                )
            )

        # 4) Continua fluxo normal (menus/dialogs)
        await DialogHelper.run_dialog(
            self.dialog,
            turn_context,
            self.conversation_state.create_property("MainDialogState"),
        )

    async def on_members_added_activity(
        self,
        members_added: ChannelAccount,
        turn_context: TurnContext,
    ):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    MessageFactory.text(
                        "Seja bem-vindo(a) ao bot de Reservas de Viagem! 🌎"
                    )
                )
                await turn_context.send_activity(
                    MessageFactory.text(
                        "Você pode falar coisas como:\n"
                        "- 'Quero comprar passagem de avião de São Paulo para o Rio'\n"
                        "- 'Quero consultar voo pra SP semana que vem'\n"
                        "- 'Quero reservar hotel no Rio amanhã para 2 pessoas'\n"
                        "- 'Quero cancelar meu hotel'\n"
                        "Ou simplesmente digitar qualquer coisa pra abrir o menu de opções."
                    )
                )

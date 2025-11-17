from botbuilder.core import ActivityHandler, TurnContext, MessageFactory, UserState, ConversationState
from botbuilder.schema import ChannelAccount
from botbuilder.dialogs import Dialog
from helpers.DialogHelper import DialogHelper

import requests  # para chamar o serviço do Azure Language


# ============ CONFIGURAÇÃO DO AZURE LANGUAGE (CLU) ============

AZURE_LANGUAGE_ENDPOINT = "https://luisluis.cognitiveservices.azure.com/"
AZURE_LANGUAGE_KEY = "D3ufTnxYkBXC3jIspcSyrCiv5ciXIjWiqAg7nLlfQR98tlSSEucoJQQJ99BKACBsN54XJ3w3AAAaACOGRUig"  
AZURE_PROJECT_NAME = "ReservaHotel"      # nome do projeto no Language Studio
AZURE_DEPLOYMENT_NAME = "production"     # nome do deployment publicado


def pegar_intent_do_azure(texto: str) -> str:
    """
    Envia o texto do usuário para o Azure Language (Conversational Language Understanding)
    e devolve o nome da intent (ex: ComprarPassagem, CancelarHotel, ReservarHotel).
    """
    if not texto:
        return "None"

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
        return top_intent
    except Exception as e:
        # Se der erro, loga no console e devolve "None" para não quebrar o bot
        print("Erro chamando Azure Language:", e)
        return "None"


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

        # Salvar alterações de estado da conversa e do usuário
        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    async def on_message_activity(self, turn_context: TurnContext):
        # Texto digitado pelo usuário
        texto_usuario = turn_context.activity.text or ""

        # 1) Descobre a intent no Azure
        intent = pegar_intent_do_azure(texto_usuario)

        # 2) Responde para o usuário qual intent foi entendida
        #    (isso já prova a integração com o Language Understanding)
        await turn_context.send_activity(
            MessageFactory.text(f"Entendi que você quer: {intent}")
        )

        # 3) Continua o fluxo normal do bot (diálogos/menus do professor)
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
                        "Seja bem-vindo(a) ao bot de Reserva de Hotéis!"
                    )
                )
                await turn_context.send_activity(
                    MessageFactory.text(
                        "Digite uma mensagem (ex: 'quero reservar hotel') para iniciar o atendimento."
                    )
                )

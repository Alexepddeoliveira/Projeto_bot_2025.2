from botbuilder.core import ActivityHandler, TurnContext, MessageFactory, UserState, ConversationState
from botbuilder.schema import ChannelAccount
from botbuilder.dialogs import Dialog
from helpers.DialogHelper import DialogHelper

import requests

from helpers.amadeus_helper import consultar_voos_demo, consultar_hoteis_demo
from helpers.databse_helper import salvar_nova_reserva  # mesmo helper usado no diálogo de novas reservas


# ============ CONFIGURAÇÃO DO AZURE LANGUAGE (CLU) ============

AZURE_LANGUAGE_ENDPOINT = "https://luisluis.cognitiveservices.azure.com/"
AZURE_LANGUAGE_KEY = "D3ufTnxYkBXC3jIspcSyrCiv5ciXIjWiqAg7nLlfQR98tlSSEucoJQQJ99BKACBsN54XJ3w3AAAaACOGRUig"
AZURE_PROJECT_NAME = "ReservaHotel"
AZURE_DEPLOYMENT_NAME = "production"


# Intents “oficiais” do trabalho
INTENTS_VOO = {"ComprarVoo", "ConsultarVoo", "CancelarVoo"}
INTENTS_HOTEL = {"ReservarHotel", "ConsultarHotel", "CancelarHotel"}

# Mapa: nomes que vêm do Azure → nomes padronizados
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

# Nome da propriedade de estado usada para guardar o fluxo de reserva
RESERVATION_CONTEXT_PROP = "ReservationContext"


def _deve_usar_clu(texto: str) -> bool:
    """
    Decide se vamos chamar o Azure CLU ou não.

    Ideia:
    - Só usamos CLU quando o texto parece um PEDIDO de viagem,
      tipo 'quero reservar hotel', 'quero comprar passagem', etc.
    - Se for coisa de formulário ('Rio de janeiro', '3') ou texto de menu
      ('Reservar viagem', 'Consultar reserva'), a gente NÃO chama CLU/Amadeus.
    """
    if not texto:
        return False

    t = texto.lower().strip()

    # Frases EXATAS do menu (ChoicePrompt) – quem cuida disso são os diálogos.
    if t in ["reservar viagem", "consultar reserva", "editar reserva", "cancelar reserva", "ajuda"]:
        return False

    # respostas curtinhas tipo "ok", "sim", "3"
    if len(t.split()) <= 2:
        return False

    # palavras-chave típicas de intenção de viagem
    keywords = [
        "quero",
        "comprar",
        "reservar",
        "cancelar",
        "alterar",
        "consultar",
        "voo",
        "vôo",
        "avião",
        "aviao",
        "passagem",
        "hotel",
        "hospedagem",
    ]

    return any(k in t for k in keywords)


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


def _extrair_detalhes(tokens):
    """
    Extrai de forma simples alguns campos dos tokens do CLU:
    cidade, data, numero de pessoas.
    """
    info = {}
    for t in tokens:
        cat = (t.get("category") or "").lower()
        txt = (t.get("text") or "").strip()
        if not txt:
            continue
        info[cat] = txt

    cidade = next((v for k, v in info.items() if "cidade" in k), None)
    data = next((v for k, v in info.items() if "data" in k), None)
    pessoas = next((v for k, v in info.items() if "pessoa" in k or "numero" in k), None)

    return {
        "cidade": cidade,
        "data": data,
        "pessoas": pessoas,
    }


def _resumir_tokens(tokens):
    """
    Monta uma frase amigável com base nos tokens:
    'em X, na data Y, para Z pessoas'
    """
    detalhes = _extrair_detalhes(tokens)
    cidade = detalhes["cidade"]
    data = detalhes["data"]
    pessoas = detalhes["pessoas"]

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

    # ========= Helpers de contexto de reserva =========

    async def _get_reservation_context(self, turn_context: TurnContext) -> dict:
        prop = self.conversation_state.create_property(RESERVATION_CONTEXT_PROP)
        ctx = await prop.get(turn_context, {})
        if ctx is None or not isinstance(ctx, dict):
            ctx = {}
            await prop.set(turn_context, ctx)
        return ctx

    async def _set_reservation_context(self, turn_context: TurnContext, ctx: dict):
        prop = self.conversation_state.create_property(RESERVATION_CONTEXT_PROP)
        if ctx is None:
            ctx = {}
        await prop.set(turn_context, ctx)

    async def _enviar_resumo_e_menu(self, turn_context: TurnContext, ctx: dict):
        """
        SALVA a reserva no banco e envia o resumo com:
        - ID (do banco)
        - destino
        - data
        - pessoas
        - opção escolhida (1/2/3)
        Depois orienta o usuário a usar o menu para futuras operações.
        """
        tipo = ctx.get("tipo")  # "voo" ou "hotel"
        destino = ctx.get("cidade") or "destino não informado"
        data = ctx.get("data") or "data não informada"
        pessoas = ctx.get("pessoas") or "quantidade não informada"
        opcao = ctx.get("chosen_option")

        # Prepara dados no formato esperado pelo banco
        # A tabela tem: destino, hospedes, chegada, saida
        # Aqui usamos a mesma data como chegada/saída (ilustrativo)
        reserva_data = {
            "destino": destino,
            "hospedes": pessoas,
            "chegada": data,
            "saida": data,
        }

        print(f"DEBUG: Enviando dados para o banco a partir do fluxo CLU/Amadeus: {reserva_data}")
        novo_id_do_banco = salvar_nova_reserva(reserva_data)

        if not novo_id_do_banco:
            await turn_context.send_activity(
                MessageFactory.text(
                    "Tentei salvar sua reserva no banco de dados, mas aconteceu um erro. "
                    "Por favor, tente novamente mais tarde ou use o menu de Reservar viagem."
                )
            )
            # Mesmo assim, mostra o menu
            ctx.clear()
            await self._set_reservation_context(turn_context, ctx)
            await DialogHelper.run_dialog(
                self.dialog,
                turn_context,
                self.conversation_state.create_property("MainDialogState"),
            )
            return

        # Se salvou, monta o resumo
        if tipo == "voo":
            titulo = "Resumo da sua reserva de VOOS:"
            label_pessoas = "Número de pessoas"
        else:
            titulo = "Resumo da sua reserva de HOTEL:"
            label_pessoas = "Número de hóspedes"

        detalhes_linha_opcao = ""
        if opcao in ["1", "2", "3"]:
            detalhes_linha_opcao = f"\n- Opção escolhida na lista da Amadeus: **{opcao}**"

        await turn_context.send_activity(
            MessageFactory.text(
                f"{titulo}\n\n"
                f"- Número da reserva (ID do banco): **{novo_id_do_banco}**\n"
                f"- Destino: **{destino}**\n"
                f"- Data: **{data}**\n"
                f"- {label_pessoas}: **{pessoas}**"
                f"{detalhes_linha_opcao}"
            )
        )

        await turn_context.send_activity(
            MessageFactory.text(
                "Sua reserva foi registrada com sucesso no nosso sistema! ✅\n"
                "Você pode consultar, editar ou cancelar essa reserva usando o ID acima "
                "pelas opções do menu (Consultar reserva, Editar reserva, Cancelar reserva)."
            )
        )

        # Limpa o contexto de reserva
        ctx.clear()
        await self._set_reservation_context(turn_context, ctx)

        # Depois disso, deixa os diálogos mostrarem o menu / formulários
        await DialogHelper.run_dialog(
            self.dialog,
            turn_context,
            self.conversation_state.create_property("MainDialogState"),
        )

    async def _handle_reservation_flow(self, turn_context: TurnContext, ctx: dict, texto_usuario: str) -> bool:
        """
        Trata as fases pós-Amadeus:
        - escolha de opção (1, 2 ou 3)
        - pedir data, se faltar
        - pedir número de pessoas, se faltar
        Retorna True se tratou a mensagem aqui (ou seja, NÃO deve cair no fluxo CLU de novo).
        """
        phase = ctx.get("phase")
        texto = (texto_usuario or "").strip()

        # Fase 1: esperando escolha da opção (1, 2 ou 3)
        if phase == "awaiting_choice":
            if texto not in ["1", "2", "3"]:
                await turn_context.send_activity(
                    MessageFactory.text("Por favor, escolha uma opção válida: **1**, **2** ou **3**.")
                )
                return True  # ainda nessa fase

            ctx["chosen_option"] = texto

            falta_data = not ctx.get("data")
            falta_pessoas = not ctx.get("pessoas")

            if falta_data:
                ctx["phase"] = "awaiting_date"
                await self._set_reservation_context(turn_context, ctx)
                await turn_context.send_activity(
                    MessageFactory.text("Informe a **data da viagem** (por exemplo: 2025-12-01).")
                )
                return True

            if falta_pessoas:
                ctx["phase"] = "awaiting_people"
                await self._set_reservation_context(turn_context, ctx)
                await turn_context.send_activity(
                    MessageFactory.text("Informe **quantas pessoas/hóspedes** vão na viagem.")
                )
                return True

            # Já temos tudo
            await self._enviar_resumo_e_menu(turn_context, ctx)
            return True

        # Fase 2: esperando data
        if phase == "awaiting_date":
            if texto:
                ctx["data"] = texto
            falta_pessoas = not ctx.get("pessoas")

            if falta_pessoas:
                ctx["phase"] = "awaiting_people"
                await self._set_reservation_context(turn_context, ctx)
                await turn_context.send_activity(
                    MessageFactory.text("Agora me diga **quantas pessoas/hóspedes** vão na viagem.")
                )
                return True

            # Já temos tudo
            await self._enviar_resumo_e_menu(turn_context, ctx)
            return True

        # Fase 3: esperando número de pessoas
        if phase == "awaiting_people":
            if texto:
                ctx["pessoas"] = texto
            falta_data = not ctx.get("data")

            if falta_data:
                ctx["phase"] = "awaiting_date"
                await self._set_reservation_context(turn_context, ctx)
                await turn_context.send_activity(
                    MessageFactory.text("Agora informe a **data da viagem** (por exemplo: 2025-12-01).")
                )
                return True

            # Já temos tudo
            await self._enviar_resumo_e_menu(turn_context, ctx)
            return True

        # Se não está em nenhuma fase nossa, retorna False pra seguir o fluxo normal
        return False

    async def on_message_activity(self, turn_context: TurnContext):
        texto_usuario = turn_context.activity.text or ""

        # Recupera (ou cria) o contexto de reserva da conversa
        ctx = await self._get_reservation_context(turn_context)

        # Se estamos em algum passo do fluxo de reserva (escolha/data/pessoas),
        # tratamos aqui ANTES de chamar CLU ou diálogos.
        if ctx.get("phase"):
            handled = await self._handle_reservation_flow(turn_context, ctx, texto_usuario)
            if handled:
                # contexto já foi usado/atualizado dentro do fluxo
                await self._set_reservation_context(turn_context, ctx)
                return

        # 0) Se a mensagem NÃO tem cara de pedido de viagem,
        #    deixa só os diálogos cuidarem (formulários, menu, etc.)
        if not _deve_usar_clu(texto_usuario):
            await DialogHelper.run_dialog(
                self.dialog,
                turn_context,
                self.conversation_state.create_property("MainDialogState"),
            )
            return

        # 1) CLU: intent + tokens
        intent_bruta, tokens = pegar_intent_e_tokens_do_azure(texto_usuario)
        intent = INTENT_ALIAS_MAP.get(intent_bruta, intent_bruta)

        print(f"DEBUG intent_bruta={intent_bruta} intent_mapeada={intent}")

        resumo_tokens = _resumir_tokens(tokens)
        detalhes = _extrair_detalhes(tokens)
        acao = _descricao_acao(intent)

        if intent in INTENTS_VOO or intent in INTENTS_HOTEL:
            msg_inicial = f"Beleza! Entendi que você quer {acao}{resumo_tokens}."
            await turn_context.send_activity(MessageFactory.text(msg_inicial))

        # 2) Integração com Amadeus + início do fluxo de reserva

        if intent in INTENTS_VOO:
            # Passo 1: buscar opções reais no Amadeus
            await turn_context.send_activity(
                MessageFactory.text("Vou consultar algumas opções de voo pra você na API da Amadeus 🚀...")
            )
            resultado_voos = consultar_voos_demo()

            # Passo 2: mostrar as opções encontradas
            await turn_context.send_activity(
                MessageFactory.text(
                    "Encontrei essas opções de voo:\n"
                    "Considere as três primeiras como **Opção 1**, **Opção 2** e **Opção 3**."
                )
            )
            await turn_context.send_activity(MessageFactory.text(resultado_voos))

            # Perguntar explicitamente qual opção ele quer
            await turn_context.send_activity(
                MessageFactory.text(
                    "Qual opção de voo você deseja? Responda com **1**, **2** ou **3**."
                )
            )

            # Prepara o contexto de reserva
            ctx = {
                "phase": "awaiting_choice",
                "tipo": "voo",
                "cidade": detalhes.get("cidade"),
                "data": detalhes.get("data"),
                "pessoas": detalhes.get("pessoas"),
            }
            await self._set_reservation_context(turn_context, ctx)
            return

        elif intent in INTENTS_HOTEL:
            # Passo 1: buscar hotéis reais no Amadeus
            await turn_context.send_activity(
                MessageFactory.text("Vou consultar alguns hotéis pra você usando a API da Amadeus 🏨...")
            )
            resultado_hoteis = consultar_hoteis_demo()

            # Passo 2: mostrar as opções encontradas
            await turn_context.send_activity(
                MessageFactory.text(
                    "Olha algumas opções de hotel que encontrei:\n"
                    "Considere as três primeiras como **Opção 1**, **Opção 2** e **Opção 3**."
                )
            )
            await turn_context.send_activity(MessageFactory.text(resultado_hoteis))

            # Perguntar explicitamente qual opção ele quer
            await turn_context.send_activity(
                MessageFactory.text(
                    "Qual opção de hotel você deseja? Responda com **1**, **2** ou **3**."
                )
            )

            # Prepara o contexto de reserva
            ctx = {
                "phase": "awaiting_choice",
                "tipo": "hotel",
                "cidade": detalhes.get("cidade"),
                "data": detalhes.get("data"),
                "pessoas": detalhes.get("pessoas"),
            }
            await self._set_reservation_context(turn_context, ctx)
            return

        else:
            await turn_context.send_activity(
                MessageFactory.text(
                    "Não entendi exatamente se é voo ou hotel, então vou te mostrar o menu de reservas 🙂"
                )
            )
            # Cai pro fluxo de diálogos
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

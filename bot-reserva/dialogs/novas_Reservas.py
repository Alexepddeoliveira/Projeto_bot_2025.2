import uuid
from botbuilder.core import MessageFactory, UserState
from botbuilder.dialogs import ComponentDialog, WaterfallDialog, WaterfallStepContext
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions


class novasReservasDialogo(ComponentDialog):
    def __init__(self, user_state: UserState):
        super(novasReservasDialogo, self).__init__("novasReservasDialogo")

        # Guarda na memória onde o usuário parou no diálogo
        self.user_state = user_state

        # Prompts utilizados neste diálogo
        self.add_dialog(TextPrompt(TextPrompt.__name__))

        # Fluxo em vários passos
        self.add_dialog(
            WaterfallDialog(
                "novasReservasDialogo",
                [
                    self.prompt_destino_step,
                    self.process_destino_step,
                    self.prompt_hospedes_step,
                    self.process_hospedes_step,
                    self.prompt_chegada_step,
                    self.process_chegada_step,
                    self.prompt_saida_step,
                    self.process_saida_step,
                    self.resumo_step,
                ],
            )
        )

        self.initial_dialog_id = "novasReservasDialogo"

    async def prompt_destino_step(self, step_context: WaterfallStepContext):
        await step_context.context.send_activity(
            MessageFactory.text("Você está iniciando uma NOVA reserva de hotel.")
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text(
                    "Para começar, por favor digite **o destino da viagem** (cidade/UF):"
                )
            ),
        )

    async def process_destino_step(self, step_context: WaterfallStepContext):
        step_context.values["destino"] = step_context.result
        await step_context.context.send_activity(
            MessageFactory.text(f"Perfeito! Destino informado: **{step_context.result}**.")
        )
        return await step_context.next(None)

    async def prompt_hospedes_step(self, step_context: WaterfallStepContext):
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Agora me diga, quantos hóspedes serão?")),
        )

    async def process_hospedes_step(self, step_context: WaterfallStepContext):
        step_context.values["hospedes"] = step_context.result
        await step_context.context.send_activity(
            MessageFactory.text(f"Ótimo! Serão **{step_context.result}** hóspedes.")
        )
        return await step_context.next(None)

    async def prompt_chegada_step(self, step_context: WaterfallStepContext):
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Qual será o dia da sua **chegada**?")),
        )

    async def process_chegada_step(self, step_context: WaterfallStepContext):
        step_context.values["chegada"] = step_context.result
        await step_context.context.send_activity(
            MessageFactory.text(f"Registrado! Chegada em **{step_context.result}**.")
        )
        return await step_context.next(None)

    async def prompt_saida_step(self, step_context: WaterfallStepContext):
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("E qual será o dia da sua **saída**?")),
        )

    async def process_saida_step(self, step_context: WaterfallStepContext):
        step_context.values["saida"] = step_context.result
        await step_context.context.send_activity(
            MessageFactory.text(f"Saída em **{step_context.result}**.")
        )
        return await step_context.next(None)

    async def resumo_step(self, step_context: WaterfallStepContext):
        destino = step_context.values["destino"]
        hospedes = step_context.values["hospedes"]
        chegada = step_context.values["chegada"]
        saida = step_context.values["saida"]

        # Cria ID único para a reserva
        reserva_id = str(uuid.uuid4())[:8]  # só os 8 primeiros caracteres para ficar curto
        step_context.values["reserva_id"] = reserva_id

        resumo = (
            f"Resumo da sua reserva:\n"
            f"- Número da reserva: **{reserva_id}**\n"
            f"- Destino: **{destino}**\n"
            f"- Hóspedes: **{hospedes}**\n"
            f"- Chegada: **{chegada}**\n"
            f"- Saída: **{saida}**"
        )

        await step_context.context.send_activity(MessageFactory.text(resumo))
        await step_context.context.send_activity(
            MessageFactory.text("Sua reserva foi registrada com sucesso!")
        )

        return await step_context.end_dialog()

from botbuilder.core import MessageFactory, UserState
from botbuilder.dialogs import ComponentDialog, WaterfallDialog, WaterfallStepContext
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions

from helpers.databse_helper import deletar_reserva

class DeletarReservaDialogo(ComponentDialog):
    def __init__(self, user_state: UserState):
        super(DeletarReservaDialogo, self).__init__(__class__.__name__)
        
        self.user_state = user_state
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        
        self.add_dialog(
            WaterfallDialog(
                "WaterfallDialog",
                [
                    self.prompt_id_step,
                    self.process_delete_step
                ]
            )
        )
        self.initial_dialog_id = "WaterfallDialog"

    async def prompt_id_step(self, step_context: WaterfallStepContext):
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Por favor, digite o número (ID) da reserva que você deseja DELETAR."))
        )

    async def process_delete_step(self, step_context: WaterfallStepContext):
        reserva_id_str = step_context.result.strip()
        
        try:
            reserva_id = int(reserva_id_str)
        except ValueError:
            await step_context.context.send_activity(MessageFactory.text(f"O ID '{reserva_id_str}' não é um número válido."))
            return await step_context.end_dialog()

        print(f"DEBUG: Tentando deletar a reserva com ID {reserva_id}.")
        sucesso = deletar_reserva(reserva_id)
        
        if sucesso:
            await step_context.context.send_activity(
                MessageFactory.text(f"A reserva com ID **{reserva_id}** foi deletada com sucesso.")
            )
        else:
            await step_context.context.send_activity(
                MessageFactory.text(f"Não foi possível deletar a reserva com ID **{reserva_id}**. Verifique se o número está correto.")
            )

        return await step_context.end_dialog()
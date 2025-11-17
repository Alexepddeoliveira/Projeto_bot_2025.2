from botbuilder.core import MessageFactory, UserState
from botbuilder.dialogs import ComponentDialog, WaterfallDialog, WaterfallStepContext
from botbuilder.dialogs.prompts import ChoicePrompt, PromptOptions
from botbuilder.dialogs.choices import Choice

from .consultar_reserva import ConsultarReservaDialogo
from .novas_Reservas import novasReservasDialogo
from .editar_Reservas import EditarReservasDialogo
from .deletar_reserva_dialogo import DeletarReservaDialogo


class MainDialog(ComponentDialog):
    def __init__(self, user_state: UserState):
        super(MainDialog, self).__init__(__class__.__name__)
        
        self.user_state = user_state
        self.add_dialog(ChoicePrompt(ChoicePrompt.__name__))

        # Diálogos de CRUD de reservas internas (banco/local)
        self.add_dialog(EditarReservasDialogo(self.user_state))
        self.add_dialog(ConsultarReservaDialogo(self.user_state))
        self.add_dialog(novasReservasDialogo(self.user_state))
        self.add_dialog(DeletarReservaDialogo(self.user_state))
        
        self.add_dialog(
            WaterfallDialog(
                "MainWaterfall",
                [
                    self.prompt_option_step,
                    self.process_option_step
                ]
            )
        )
        self.initial_dialog_id = "MainWaterfall"
    
    async def prompt_option_step(self, step_context: WaterfallStepContext):
        """
        Menu principal do bot para gerenciar as reservas SALVAS no sistema.
        A parte de entendimento de linguagem + Amadeus já acontece antes,
        aqui o usuário só gerencia o que ficou registrado.
        """
        return await step_context.prompt(
            ChoicePrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text(
                    "Agora vamos falar das suas reservas salvas no sistema.\n\n"
                    "O que você quer fazer?"
                ),
                choices=[
                    Choice("Novas Reservas"),
                    Choice("Consultar Reservas"),
                    Choice("Editar Reservas"),
                    Choice("Deletar Reservas"),
                    Choice("Ajuda"),
                ],
            ),
        )

    async def process_option_step(self, step_context: WaterfallStepContext):
        option = step_context.result.value
        
        if option == "Novas Reservas":
            return await step_context.begin_dialog(novasReservasDialogo.__name__)
            
        elif option == "Consultar Reservas":
            return await step_context.begin_dialog(ConsultarReservaDialogo.__name__)
            
        elif option == "Editar Reservas":
            return await step_context.begin_dialog(EditarReservasDialogo.__name__)
        
        elif option == "Deletar Reservas":
            return await step_context.begin_dialog(DeletarReservaDialogo.__name__)
            
        elif option == "Ajuda":
            await step_context.context.send_activity(
                MessageFactory.text(
                    "Você pode usar este menu para registrar, consultar, editar ou deletar "
                    "reservas do sistema interno (tanto de hotel quanto de voo, se você quiser "
                    "guardar essas informações aqui)."
                )
            )
            return await step_context.replace_dialog(self.id)

        # Qualquer coisa fora das opções, reabre o menu
        return await step_context.replace_dialog(self.id)

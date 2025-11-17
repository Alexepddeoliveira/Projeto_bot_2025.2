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

        # Diálogos de CRUD de reservas internas
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
        Menu principal para gerenciar as reservas SALVAS no sistema interno.
        As opções já usam frases parecidas com as que o usuário falaria.
        """
        return await step_context.prompt(
            ChoicePrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text(
                    "Agora vamos falar das suas reservas salvas no sistema.\n\n"
                    "Escolha uma opção:"
                ),
                choices=[
                    Choice("Reservar viagem"),      # antes: Novas Reservas
                    Choice("Consultar reserva"),    # antes: Consultar Reservas
                    Choice("Editar reserva"),       # antes: Editar Reservas
                    Choice("Cancelar reserva"),     # antes: Deletar Reservas
                    Choice("Ajuda"),
                ],
            ),
        )

    async def process_option_step(self, step_context: WaterfallStepContext):
        option = step_context.result.value
        
        if option == "Reservar viagem":
            return await step_context.begin_dialog(novasReservasDialogo.__name__)
            
        elif option == "Consultar reserva":
            return await step_context.begin_dialog(ConsultarReservaDialogo.__name__)
            
        elif option == "Editar reserva":
            return await step_context.begin_dialog(EditarReservasDialogo.__name__)
        
        elif option == "Cancelar reserva":
            return await step_context.begin_dialog(DeletarReservaDialogo.__name__)
            
        elif option == "Ajuda":
            await step_context.context.send_activity(
                MessageFactory.text(
                    "Você pode usar este menu para registrar, consultar, editar ou cancelar "
                    "reservas que já estão salvas no sistema interno."
                )
            )
            return await step_context.replace_dialog(self.id)

        # Qualquer coisa fora das opções, reabre o menu
        return await step_context.replace_dialog(self.id)

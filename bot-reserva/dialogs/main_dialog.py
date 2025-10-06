
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
        
        # Registrando todos os diálogos com os nomes padronizados
        self.add_dialog(EditarReservasDialogo(self.user_state))
        self.add_dialog(ConsultarReservaDialogo(self.user_state))
        self.add_dialog(novasReservasDialogo(self.user_state))
        self.add_dialog(DeletarReservaDialogo(self.user_state)) # <-- Novo diálogo adicionado
        
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
        # 3. Adicionada a opção "Deletar Reservas" no menu
        return await step_context.prompt(
            ChoicePrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Seja bem-vindo(a) ao bot de reservas! Escolha a opção desejada:"),
                choices=[
                    Choice("Novas Reservas"),
                    Choice("Consultar Reservas"),
                    Choice("Editar Reservas"),
                    Choice("Deletar Reservas"), # <-- Nova opção
                    Choice("Ajuda")
                ]
            )
        )

    async def process_option_step(self, step_context: WaterfallStepContext):
        option = step_context.result.value
        
        # Lógica atualizada para chamar os diálogos pelos seus nomes de classe
        if (option == "Novas Reservas"):
            return await step_context.begin_dialog(novasReservasDialogo.__name__)
            
        elif (option == "Consultar Reservas"):
            return await step_context.begin_dialog(ConsultarReservaDialogo.__name__)
            
        elif (option == "Editar Reservas"):
            return await step_context.begin_dialog(EditarReservasDialogo.__name__)
        
        elif (option == "Deletar Reservas"): # <-- Nova lógica
            return await step_context.begin_dialog(DeletarReservaDialogo.__name__)
            
        elif (option == "Ajuda"):
            await step_context.context.send_activity(MessageFactory.text("Você escolheu a opção Ajuda. Em que posso ser útil?"))
            # Reinicia o diálogo principal para mostrar o menu novamente
            return await step_context.replace_dialog(self.id)

        # Se a opção não for reconhecida, apenas reinicia o diálogo.
        return await step_context.replace_dialog(self.id)
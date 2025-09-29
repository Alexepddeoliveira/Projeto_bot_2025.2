from botbuilder.core import MessageFactory, UserState
from botbuilder.dialogs import ComponentDialog, WaterfallDialog, WaterfallStepContext
from botbuilder.dialogs.prompts import ChoicePrompt, PromptOptions
from botbuilder.dialogs.choices import Choice 
from dialogs.consultar_reserva import consultarReservaDialogo
from dialogs.novas_Reservas import novasReservasDialogo
from dialogs.editar_Reservas import editarReservasDialogo

class MainDialog(ComponentDialog):
    
    def __init__(self, user_state: UserState):
        super(MainDialog, self).__init__("MainDialog")
        
        #Guarda na memoria aonde o usuário parou no dialogo
        self.user_state = user_state
        
        #Prompt para escolher as opções de atendimento
        self.add_dialog(ChoicePrompt(ChoicePrompt.__name__))
        
        self.add_dialog(editarReservasDialogo(self.user_state))
        self.add_dialog(consultarReservaDialogo(self.user_state))
        self.add_dialog(novasReservasDialogo(self.user_state))
        
        #Conversação Sequencial (Steps)        
        self.add_dialog(
            WaterfallDialog(
                "MainDialog",
                [
                    self.prompt_option_step,
                    self.process_option_step
                ]
            )
        )
        
        self.initial_dialog_id = "MainDialog"
    
    async def prompt_option_step(self, step_context: WaterfallStepContext):
        return await step_context.prompt(
            ChoicePrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Escolha a opção desejada:"),
                choices=[
                    Choice("Editar Reservas"),
                    Choice("Consultar Reservas"),
                    Choice("Novas Reservas"),
                    Choice("Ajuda")
                ]
            )
        )
    async def process_option_step(self, step_context: WaterfallStepContext):
        #Captura o que o usuário escolheu de opcao
        option = step_context.result.value
        
        if (option == "Editar Reservas"):
           return await step_context.begin_dialog("editarReservasDialogo")
    
        elif (option == "Consultar Reservas"):
            return await step_context.begin_dialog("consultarReservaDialogo")
                    
                
        elif (option == "Novas Reservas"):
            return await step_context.begin_dialog("novasReservasDialogo")
                
        elif (option == "Ajuda"):
            return await step_context.context.send_activity(
                    MessageFactory.text(
                        "Voce escolheu a opção Ajuda"
                    )
                )
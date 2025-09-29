from botbuilder.core import MessageFactory, UserState
from botbuilder.dialogs import ComponentDialog, WaterfallDialog, WaterfallStepContext
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions

class consultarReservaDialogo(ComponentDialog):
    def __init__(self, user_state: UserState):
        super(consultarReservaDialogo, self).__init__("consultarReservaDialogo")
        
        #Guarda na memoria aonde o usuário parou no dialogo
        self.user_state = user_state
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        
        self.add_dialog(
            WaterfallDialog(
                "consultarReservaDialogo",
                [
                    self.prompt_CPF_step,
                    self.process_CPF_step
                ]
            )
        )
    
        self.initial_dialog_id = "consultarReservaDialogo"
    async def prompt_CPF_step(self, step_context: WaterfallStepContext):
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=MessageFactory.text("Por favor digite seu CPF para consultar suas reservas"))
            )
    async def process_CPF_step(self, step_context: WaterfallStepContext):
        cpf = step_context.result
        #TODO:Criar logica de consulta ao backend para o cpf
        
        return await step_context.end_dialog()
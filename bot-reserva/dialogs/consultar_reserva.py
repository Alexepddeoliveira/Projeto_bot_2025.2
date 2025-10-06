from botbuilder.core import MessageFactory, UserState
from botbuilder.dialogs import ComponentDialog, WaterfallDialog, WaterfallStepContext
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions

from helpers.databse_helper import buscar_reserva_por_id

class ConsultarReservaDialogo(ComponentDialog): # Renomeado para seguir o padrão de nomes de classes
    def __init__(self, user_state: UserState):
        super(ConsultarReservaDialogo, self).__init__(__class__.__name__) # Usando o nome da classe como ID
        
        self.user_state = user_state
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        
        self.add_dialog(
            WaterfallDialog(
                "WaterfallDialog", # ID interno
                [
                    self.prompt_id_step,    # 2. Renomeado o passo
                    self.process_id_step   # 3. Renomeado o passo
                ]
            )
        )
    
        self.initial_dialog_id = "WaterfallDialog"

    async def prompt_id_step(self, step_context: WaterfallStepContext):
        # Mensagem do prompt atualizada
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text("Por favor, digite o número (ID) da reserva que deseja consultar."))
        )

    async def process_id_step(self, step_context: WaterfallStepContext):
        # Lógica totalmente atualizada para buscar por ID
        reserva_id_str = step_context.result.strip()
        
        try:
            # Tenta converter a entrada do usuário para um número inteiro
            reserva_id = int(reserva_id_str)
        except ValueError:
            # Se não for um número, avisa o usuário e encerra.
            await step_context.context.send_activity(
                MessageFactory.text(f"O ID '{reserva_id_str}' não é um número válido. Por favor, inicie a consulta novamente com um ID numérico.")
            )
            return await step_context.end_dialog()
            
        print(f"DEBUG: Iniciando consulta no diálogo para o ID {reserva_id}.")
        reserva = buscar_reserva_por_id(reserva_id)
        
        if not reserva:
            await step_context.context.send_activity(
                MessageFactory.text(f"Não encontrei nenhuma reserva com o ID **{reserva_id}**.")
            )
        else:
            await step_context.context.send_activity(
                MessageFactory.text(f"Encontrei a reserva **{reserva_id}**:")
            )
            
            # Formata e envia a reserva encontrada
            resumo = (
                f"- Destino: **{reserva.get('destino', 'N/D')}**\n"
                f"- Hóspedes: **{reserva.get('hospedes', 'N/D')}**\n"
                f"- Chegada: **{reserva.get('chegada', 'N/D')}**\n"
                f"- Saída: **{reserva.get('saida', 'N/D')}**"
            )
            await step_context.context.send_activity(MessageFactory.text(resumo))

        return await step_context.end_dialog()
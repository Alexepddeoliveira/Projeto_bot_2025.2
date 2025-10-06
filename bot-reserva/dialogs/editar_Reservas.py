from botbuilder.core import MessageFactory, UserState
from botbuilder.dialogs import ComponentDialog, WaterfallDialog, WaterfallStepContext
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions, ChoicePrompt
from botbuilder.dialogs.choices import Choice, ListStyle

from helpers.databse_helper import buscar_reserva_por_id, atualizar_reserva

class EditarReservasDialogo(ComponentDialog):
    def __init__(self, user_state: UserState):
        super(EditarReservasDialogo, self).__init__(__class__.__name__)

        # Guarda na memória onde o usuário parou no diálogo
        self.user_state = user_state

        # Prompts 
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(ChoicePrompt(ChoicePrompt.__name__))

        self.add_dialog(
            WaterfallDialog(
                "WaterfallDialog",
                [
                    self.prompt_identificador_step,
                    self.process_identificador_step,
                    self.prompt_menu_step,
                    self.route_choice_step,
                    self.prompt_edit_field_step,
                    self.process_edit_field_step,
                    self.prompt_continue_step,
                    self.route_continue_step,
                    self.resumo_step,
                ],
            )
        )

        self.initial_dialog_id = "WaterfallDialog"

    # Pede o ID da reserva
    async def prompt_identificador_step(self, step_context: WaterfallStepContext):
        if getattr(step_context, "options", None):
            opts = step_context.options or {}
            if "reserva_atual" in opts and "reserva_editada" in opts and "identificador" in opts:
                step_context.values["reserva_atual"] = opts["reserva_atual"]
                step_context.values["reserva_editada"] = opts["reserva_editada"]
                step_context.values["identificador"] = opts["identificador"]
                return await step_context.next("skip-identificador")

        await step_context.context.send_activity(
            MessageFactory.text("Você escolheu **editar uma reserva existente**.")
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text(
                    "Por favor, digite o **número (ID) da reserva** que deseja editar:"
                )
            ),
        )

    # Busca a reserva no banco de dados
    async def process_identificador_step(self, step_context: WaterfallStepContext):
        if step_context.result == "skip-identificador":
            return await step_context.next(None)

        identificador_str = (step_context.result or "").strip()
        
        try:
            identificador = int(identificador_str)
        except ValueError:
            await step_context.context.send_activity(MessageFactory.text(f"O ID '{identificador_str}' não é um número válido."))
            return await step_context.end_dialog()

        print(f"DEBUG: Buscando reserva com ID {identificador}...")
        reserva_atual = buscar_reserva_por_id(identificador)

        if not reserva_atual:
            await step_context.context.send_activity(MessageFactory.text(f"Não encontrei nenhuma reserva com o ID **{identificador}**."))
            return await step_context.end_dialog()

        step_context.values["reserva_atual"] = reserva_atual
        step_context.values["reserva_editada"] = dict(reserva_atual)
        step_context.values["identificador"] = identificador

        await step_context.context.send_activity(MessageFactory.text(f"✅ Reserva **{identificador}** encontrada."))
        await step_context.context.send_activity(
            MessageFactory.text("Escolha abaixo **o que deseja alterar** (ou **Finalizar**):")
        )
        await step_context.context.send_activity(
            MessageFactory.text(
                f"🗂️ Dados atuais:\n"
                f"- Nº da reserva: **{reserva_atual['reserva_id']}**\n"
                f"- Destino: **{reserva_atual['destino']}**\n"
                f"- Hóspedes: **{reserva_atual['hospedes']}**\n"
                f"- Chegada: **{reserva_atual['chegada']}**\n"
                f"- Saída: **{reserva_atual['saida']}**"
            )
        )
        return await step_context.next(None)

    # Mostra o menu de opções para edição
    async def prompt_menu_step(self, step_context: WaterfallStepContext):
        return await step_context.prompt(
            ChoicePrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("O que você quer alterar?"),
                choices=[
                    Choice("Destino"),
                    Choice("Hóspedes"),
                    Choice("Chegada"),
                    Choice("Saída"),
                    Choice("Finalizar"),
                ],
                style=ListStyle.suggested_action,
            ),
        )

    # Processa a escolha do usuário
    async def route_choice_step(self, step_context: WaterfallStepContext):
        escolha = step_context.result.value if step_context.result else ""
        step_context.values["escolha_menu"] = escolha

        if escolha == "Finalizar":
            return await step_context.next("finalizar")

        campos_map = {
            "Destino": "destino",
            "Hóspedes": "hospedes",
            "Chegada": "chegada",
            "Saída": "saida",
        }
        step_context.values["campo_em_edicao"] = campos_map.get(escolha)
        return await step_context.next(None)

    # Pede o novo valor para o campo escolhido
    async def prompt_edit_field_step(self, step_context: WaterfallStepContext):
        if step_context.result == "finalizar":
            return await step_context.next("finalizar")

        campo = step_context.values.get("campo_em_edicao")
        atual = step_context.values["reserva_editada"].get(campo)
        labels = {
            "destino": "destino",
            "hospedes": "número de hóspedes",
            "chegada": "data de chegada",
            "saida": "data de saída",
        }

        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text(
                    f"Valor atual de **{labels[campo]}**: **{atual}**.\n"
                    f"Digite o novo valor ou escreva **manter** para não alterar:"
                )
            ),
        )

    # Processa o novo valor e atualiza o estado temporário
    async def process_edit_field_step(self, step_context: WaterfallStepContext):
        if step_context.result == "finalizar":
            return await step_context.next("finalizar")

        campo = step_context.values.get("campo_em_edicao")
        novo = (step_context.result or "").strip()

        if novo and novo.lower() not in ("manter", "pular", "-"):
            step_context.values["reserva_editada"][campo] = novo
            await step_context.context.send_activity(
                MessageFactory.text(f"{campo.capitalize()} atualizado para **{novo}**.")
            )
        else:
            await step_context.context.send_activity(MessageFactory.text("Sem alterações."))

        return await step_context.next(None)

    # Pergunta se o usuário quer continuar editando
    async def prompt_continue_step(self, step_context: WaterfallStepContext):
        if step_context.result == "finalizar":
            return await step_context.next("finalizar")

        return await step_context.prompt(
            ChoicePrompt.__name__,
            PromptOptions(
                prompt=MessageFactory.text("Deseja **editar mais** algum campo ou **finalizar**?"),
                choices=[Choice("Editar mais"), Choice("Finalizar")],
                style=ListStyle.suggested_action,
            ),
        )

    # Roteia a decisão de continuar ou finalizar
    async def route_continue_step(self, step_context: WaterfallStepContext):
        if step_context.result == "finalizar":
            return await step_context.next("finalizar")

        escolha = step_context.result.value if step_context.result else "Finalizar"
        if escolha == "Editar mais":
            await step_context.context.send_activity(
                MessageFactory.text("Certo! Escolha outro campo para editar:")
            )
            # Reinicia o diálogo mantendo o estado atual
            return await step_context.replace_dialog(
                self.id,
                {
                    "reserva_atual": step_context.values["reserva_atual"],
                    "reserva_editada": step_context.values["reserva_editada"],
                    "identificador": step_context.values["identificador"],
                },
            )
        else:
            return await step_context.next("finalizar")

    # Mostra o resumo final e salva as alterações no banco
    async def resumo_step(self, step_context: WaterfallStepContext):
        r = step_context.values["reserva_editada"]
        resumo = (
            "**Resumo da reserva (após edição):**\n"
            f"- Nº da reserva: **{r.get('reserva_id', 'N/D')}**\n"
            f"- Destino: **{r['destino']}**\n"
            f"- Hóspedes: **{r['hospedes']}**\n"
            f"- Chegada: **{r['chegada']}**\n"
            f"- Saída: **{r['saida']}**"
        )
        await step_context.context.send_activity(MessageFactory.text(resumo))

        # Lógica de atualização real no banco de dados
        print(f"DEBUG: Atualizando reserva ID {r['reserva_id']} com os dados: {r}")
        sucesso = atualizar_reserva(r['reserva_id'], r)

        if sucesso:
            await step_context.context.send_activity(
                MessageFactory.text("Alterações registradas com sucesso!")
            )
        else:
            await step_context.context.send_activity(
                MessageFactory.text("Desculpe, ocorreu um erro ao salvar suas alterações.")
            )

        return await step_context.end_dialog()
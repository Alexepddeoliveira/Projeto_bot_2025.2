from botbuilder.core import MessageFactory, UserState
from botbuilder.dialogs import ComponentDialog, WaterfallDialog, WaterfallStepContext
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions, ChoicePrompt
from botbuilder.dialogs.choices import Choice, ListStyle


class editarReservasDialogo(ComponentDialog):
    def __init__(self, user_state: UserState):
        super(editarReservasDialogo, self).__init__("editarReservasDialogo")

        # Guarda na memória onde o usuário parou no diálogo
        self.user_state = user_state

        # Prompts 
        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(ChoicePrompt(ChoicePrompt.__name__))

        self.add_dialog(
            WaterfallDialog(
                "editarReservasDialogo",
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

        self.initial_dialog_id = "editarReservasDialogo"

    # identificador
    async def prompt_identificador_step(self, step_context: WaterfallStepContext):
        # Se o diálogo foi reiniciado com estado (options), pulamos a coleta do identificador
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
                    "Por favor, digite o **número da reserva** (ou o **CPF** utilizado na reserva):"
                )
            ),
        )

    # Carrega dados (simulação) e inicializa estado
    async def process_identificador_step(self, step_context: WaterfallStepContext):
        # Se veio do reinício com options, já temos tudo
        if step_context.result == "skip-identificador":
            return await step_context.next(None)

        identificador = (step_context.result or "").strip()
        step_context.values["identificador"] = identificador

        # TODO: Buscar no backend pelo identificador. SIMULAÇÃO de dados atuais:
        reserva_atual = {
            "reserva_id": identificador if identificador else "RSV-2025-ABC12345",
            "destino": "Fortaleza/CE",
            "hospedes": "2",
            "chegada": "10/10/2025",
            "saida": "15/10/2025",
        }
        step_context.values["reserva_atual"] = reserva_atual
        step_context.values["reserva_editada"] = dict(reserva_atual)  # começamos iguais

        await step_context.context.send_activity(
            MessageFactory.text(f"✅ Identificador recebido: **{identificador or reserva_atual['reserva_id']}**.")
        )
        await step_context.context.send_activity(
            MessageFactory.text(
                "Encontrei sua reserva. Escolha abaixo **o que deseja alterar** (ou **Finalizar**):"
            )
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

    #botões (Suggested Actions)
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
                style=ListStyle.suggested_action,  # botões acima do composer
            ),
        )

    # Roteia a escolha do menu
    async def route_choice_step(self, step_context: WaterfallStepContext):
        escolha = step_context.result.value if step_context.result else ""
        step_context.values["escolha_menu"] = escolha

        if escolha == "Finalizar":
            # Pula para o resumo
            return await step_context.next("finalizar")

        # define qual campo editar
        campos_map = {
            "Destino": "destino",
            "Hóspedes": "hospedes",
            "Chegada": "chegada",
            "Saída": "saida",
        }
        step_context.values["campo_em_edicao"] = campos_map.get(escolha)
        return await step_context.next(None)

    # Prompt do campo escolhido
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

    # Processa a edição do campo
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

    # Pergunta se quer fazer mais alterações
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

    # Reinicia
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

    # Resumo final
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

        # TODO: Persistir alterações no backend
        await step_context.context.send_activity(
            MessageFactory.text("Alterações registradas com sucesso!")
        )

        return await step_context.end_dialog()

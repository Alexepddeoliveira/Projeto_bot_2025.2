#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

class DefaultConfig:
    """ Bot Configuration """

    PORT = 3978
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

    # =========================
    # CONFIG DO AZURE COSMOS DB
    # =========================
    # COSMOS_ENDPOINT: endereço da conta Cosmos (a "rua" do seu banco)
    # COSMOS_KEY: chave de acesso (a "chave da casa")
    # COSMOS_DATABASE: nome do database criado no Data Explorer
    # COSMOS_CONTAINER: nome do container onde ficam as reservas
    COSMOS_ENDPOINT = os.environ.get(
        "COSMOS_ENDPOINT",
        "https://chatbotdbga.documents.azure.com:443/",
    )
    COSMOS_KEY = os.environ.get(
        "COSMOS_KEY",
        "Chave ilustrativa pq o github n deixa colocar chave real aqui==",
    )
    COSMOS_DATABASE = os.environ.get("COSMOS_DATABASE", "reservas-db")
    COSMOS_CONTAINER = os.environ.get("COSMOS_CONTAINER", "reservas")

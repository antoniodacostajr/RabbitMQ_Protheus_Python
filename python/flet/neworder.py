import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import flet as ft
import pandas as pd
import os
import uuid
import json
from rabbitMQ import message
from generics import getOrders


def insertOrder(page: ft.Page):
    page.title = "Pedido de Venda"
    page.scroll = "auto"

    # Cabeçalho do pedido
    cliente_codigo = ft.Dropdown(
        label="Código do Cliente",
        width=200,
        options=[
            ft.dropdown.Option(None, "Código do Cliente"),
            ft.dropdown.Option("000001", "Empresa ME"),
            ft.dropdown.Option("000002", "Cliente Padrão"),
            ft.dropdown.Option("XXX999", "Não cadastrado. Gerar erro."),
        ],
        value=None
    )
    cliente_loja = ft.TextField(label="Loja do Cliente", width=150, value="01")
    cond_pagamento = ft.Dropdown(
        label="Condição de Pagamento",
        width=200,
        options=[
            ft.dropdown.Option("000", "À Vista"),
        ],
        value="000"
    )

    # Lista de itens do pedido
    itens = []

    def adicionar_item(e=None):
        produto_codigo = ft.Dropdown(
            label="Código do Produto",
            width=200,
            options=[
                ft.dropdown.Option("PROD-PA-001", "PRODUTO ACABADO 00A"),
                ft.dropdown.Option("PROD_PA002", "PRODUTO ACABADO 002"),
                ft.dropdown.Option("XXX999", "Produto não cadastrado. Gerar erro."),
                ],
            value=""
            )
        quantidade = ft.TextField(label="Quantidade", width=100, value="1.00", keyboard_type="number")
        valor_unitario = ft.TextField(label="Valor Unitário", width=120, value="0.00", keyboard_type="number")
        total = ft.TextField(label="Vlr. Total", value="0.00", width=100, read_only=True)
        tipo_venda = ft.Dropdown(
            label="Tipo de Venda",
            width=180,
            options=[
                ft.dropdown.Option("01", "01-Venda Mercadoria"),
                ft.dropdown.Option("04", "04-Bonificação"),
            ],
            value="01"
        )

        def calcular_total(e=None):
            try:
                q = float(quantidade.value)
                v = float(valor_unitario.value)
                total.value = f"{q * v:.2f}"
            except Exception:
                total.value = "0.00"
            page.update()
            atualizar_total_pedido()

        quantidade.on_change = calcular_total
        valor_unitario.on_change = calcular_total

        linha = ft.Row([
            produto_codigo,
            quantidade,
            valor_unitario,
            total,
            tipo_venda,
        ], alignment="spaceBetween")
        itens.append(linha)
        itens_container.controls.append(linha)
        page.update()
        atualizar_total_pedido()

    itens_container = ft.Column([])

    # Botão para adicionar item
    btn_add_item = ft.ElevatedButton("Adicionar Item", on_click=adicionar_item)

    # Card do total do pedido e botões de ação
    total_pedido = ft.TextField(label="Total do Pedido", width=200, value="0.00", read_only=True)

    def atualizar_total_pedido():
        total = 0.0
        for linha in itens:
            try:
                valor = float(linha.controls[3].value)
                total += valor
            except Exception:
                pass
        total_pedido.value = f"{total:.2f}"
        page.update()

    def limpar_tela(e=None):
        cliente_codigo.value = None
        cliente_loja.value = "01"
        cond_pagamento.value = "000"
        itens.clear()
        itens_container.controls.clear()
        total_pedido.value = "0.00"
        page.update()
        adicionar_item()

    def validar_campos():
        lsucess = True
        if not cliente_codigo.value:
            cliente_codigo.error_text = "⚠️ Código do Cliente é obrigatório!"
            lsucess = False
        else:
            cliente_codigo.error_text = None
        
        if not cliente_loja.value:
            cliente_loja.error_text = "⚠️ Loja do Cliente é obrigatória!"
            lsucess = False
        else:
            cliente_loja.error_text = None
            
        if not cond_pagamento.value:
            cond_pagamento.error_text = "⚠️ Condição de Pagamento é obrigatória!"
            lsucess = False
        else:
            cond_pagamento.error_text = None

        cliente_codigo.update()
        cliente_loja.update()
        cond_pagamento.update()
            
        for linha in itens:
            if not linha.controls[0].value:
                linha.controls[0].error_text = "⚠️ Código do Produto é obrigatório!"
                lsucess = False
            else:
                linha.controls[0].error_text = None
                
            if float(linha.controls[1].value) <= 0:
                linha.controls[1].error_text = "⚠️ Quantidade deve ser maior que 0!"
                lsucess = False
            else:
                linha.controls[1].error_text = None
                
            if float(linha.controls[2].value) <= 0:
                linha.controls[2].error_text = "⚠️ Valor Unitário deve ser maior que 0!"
                lsucess = False
            else:
                linha.controls[2].error_text = None
                
            if not linha.controls[4].value:
                linha.controls[4].error_text = "⚠️ Tipo de Venda é obrigatório!"
                lsucess = False
            else:
                linha.controls[4].error_text = None
            linha.controls[0].update()
            linha.controls[1].update()
            linha.controls[2].update()
            linha.controls[4].update()
        
        if lsucess:
            
            cliente_loja.error_text = None
            cond_pagamento.error_text = None

            cliente_codigo.update()
            cliente_loja.update()
            cond_pagamento.update()
        
        page.update()
            
        return lsucess

    def salvar_tela(e=None):
        
        def gravar_pedido(e=None):
            
            dados = []
            id = str(uuid.uuid4())
            for linha in itens:
                produto = linha.controls[0].value
                quantidade = float(linha.controls[1].value)
                valor_unitario = float(linha.controls[2].value)
                valor_total = float(linha.controls[3].value)
                tipo_venda = linha.controls[4].value
                dados.append({
                    "id": id,
                    "data": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "cliente_codigo": cliente_codigo.value,
                    "cliente_loja": cliente_loja.value,
                    "cond_pagamento": cond_pagamento.value,
                    "produto_codigo": produto,
                    "quantidade": quantidade,
                    "valor_unitario": valor_unitario,
                    "valor_total": valor_total,
                    "tipo_venda": tipo_venda,
                    "msg": "",
                    "sucess": False,
                })
                
            # Carregar todos os pedidos, para adicionar o novo pedido
            dfOrders = getOrders()
                
            dfNewOrder = pd.DataFrame(dados)
            dfOrders = pd.concat([dfOrders, dfNewOrder], ignore_index=True)
            dfOrders.to_excel("orders.xlsx", index=False)
            
            # Adicionar mensagem no RabbitMQ
            message.insert_message(
                queue_name='pedidos',
                message=json.dumps(dados, ensure_ascii=False),
            )
            
            
            dlgOk = ft.AlertDialog(
                title=ft.Text("✅ Sucesso!"),
                content=ft.Text(f"Seu pedido {id}, foi gravado com Sucesso!"),
                actions=[ft.TextButton("Ok", on_click=lambda e: page.close(dlgOk))],
                alignment=ft.alignment.center,
                title_padding=ft.padding.all(25),
                )
            
            page.open(dlgOk)
            limpar_tela()
        
        if validar_campos():
            dlgConfirm = ft.AlertDialog(
                title=ft.Text("Confirmação 🤔"),
                content=ft.Text("Deseja realmente salvar o pedido ❓"),
                actions=[
                    ft.TextButton("❌", on_click=lambda e: page.close(dlgConfirm)),
                    ft.TextButton("✅", on_click=gravar_pedido)
                ],
                alignment=ft.alignment.center,
                title_padding=ft.padding.all(25),
            )
            page.open(dlgConfirm)
            page.update()
        
        
    btn_salvar = ft.ElevatedButton("Salvar", on_click=salvar_tela, bgcolor="green", color="white")
    btn_cancelar = ft.ElevatedButton("Cancelar", on_click=limpar_tela, bgcolor="red", color="white")
    btn_browse = ft.ElevatedButton("Voltar", on_click=lambda e: page.go("/"), bgcolor="red", color="white")

    # Layout da página
    snack_bar = ft.SnackBar(content=ft.Text(""))
    page.snack_bar = snack_bar

    return [
        ft.Card(
            ft.Container(
                ft.Column([
                    ft.Text("Cabeçalho do Pedido", theme_style="headlineSmall"),
                    ft.Row([cliente_codigo, cliente_loja, cond_pagamento], alignment="start"),
                ]),
                padding=20,
            )
        ),
        ft.Card(
            ft.Container(
                ft.Column([
                    ft.Text("Itens do Pedido", theme_style="headlineSmall"),
                    itens_container,
                    btn_add_item,
                ]),
                padding=20,
            )
        ),
        ft.Row([
            ft.Card(
                ft.Container(
                    ft.Column([
                        ft.Text("Total do Pedido", theme_style="headlineSmall"),
                        total_pedido,
                    ]),
                    padding=20,
                )
            ),
            ft.Row([
                btn_salvar,
                btn_cancelar,
                btn_browse,
            ], alignment="center", spacing=10)
        ]),
    ]

def get_insert_order_view(page: ft.Page):
    return insertOrder(page)

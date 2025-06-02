import sys
import os
import pandas as pd
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import flet as ft
from generics import getOrders, refreshOrders
import neworder as neworder



def main(page: ft.Page):
    page.title = "POC de Integração Python-Flet-RabbitMQ-Protheus"
    page.scroll = "auto"

    def build_home_view():
        conteudo = [
            ft.Text(
                value="POC de Integração Python-Flet, RabbitMQ e Protheus",
                theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                text_align=ft.TextAlign.CENTER,
            )
        ]
        def abrir_novo_pedido(e=None):
            page.go("/neworder")
        def atualizar_pedidos(e=None):
            btn_atualizar_pedidos.text = "Atualizando..."
            btn_atualizar_pedidos.disabled = True
            page.update()
            refreshOrders()
            btn_atualizar_pedidos.text = "Atualizar Pedidos"
            btn_atualizar_pedidos.disabled = False
            build_home_view()  # Atualiza a tela diretamente
            page.update()
        btn_novo_pedido = ft.ElevatedButton("Novo Pedido de Venda", on_click=abrir_novo_pedido, bgcolor="blue", color="white")
        btn_atualizar_pedidos = ft.ElevatedButton("Atualizar Pedidos", on_click=atualizar_pedidos, bgcolor="orange", color="white")
        conteudo.append(ft.Row([btn_novo_pedido, btn_atualizar_pedidos], alignment=ft.MainAxisAlignment.START))
        dfOrders = getOrders()
        if dfOrders.empty:
            conteudo.append(ft.Text("Nenhum pedido encontrado."))
        else:
            dfOrders.sort_values(by='data', ascending=False, inplace=True)
            id = None
            for index, row in dfOrders.iterrows():
                if id != str(row['id']):
                    # Lógica para emoji na coluna 'Integração Protheus'
                    if row['sucess']:
                        status_emoji = "✅ Integração OK"
                    else:
                        msg_vazia = (not row['msg']) or (str(row['msg']).strip() == "") or (str(row['msg']).lower() == "nan")
                        if msg_vazia:
                            status_emoji = "🟡 Mensagem não lida"
                        else:
                            status_emoji = "❌ Erro no Processamento"
                    table = ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("ID")),
                            ft.DataColumn(ft.Text("Data")),
                            ft.DataColumn(ft.Text("Cód Cliente")),
                            ft.DataColumn(ft.Text("Loja Cliente")),
                            ft.DataColumn(ft.Text("Condição Pagamento")),
                            ft.DataColumn(ft.Text("Integração Protheus")),
                        ],
                        rows=[
                            ft.DataRow(
                                cells=[
                                    ft.DataCell(ft.Text(str(row['id']))),
                                    ft.DataCell(ft.Text(str(row['data']))),
                                    ft.DataCell(ft.Text(str(row['cliente_codigo']))),
                                    ft.DataCell(ft.Text(str(row['cliente_loja']))),
                                    ft.DataCell(ft.Text(str(row['cond_pagamento']))),
                                    ft.DataCell(ft.Text(status_emoji)),
                                ]
                            )
                        ]
                    )
                    conteudo.append(table)
                    # Itens do pedido
                    dfItens = dfOrders[dfOrders['id'] == row['id']].copy()
                    dataRows = []
                    for indexI, rowI in dfItens.iterrows():
                        dataRows.append(
                            ft.DataRow(
                                cells=[
                                    ft.DataCell(ft.Text(str(rowI['produto_codigo']))),
                                    ft.DataCell(ft.Text(str(rowI['quantidade']))),
                                    ft.DataCell(ft.Text(str(rowI['valor_unitario']))),
                                    ft.DataCell(ft.Text(str(rowI['valor_total']))),
                                    ft.DataCell(ft.Text(str(rowI['tipo_venda']))),
                                ]
                            )
                        )
                    itensTable = ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("Cód Produto")),
                            ft.DataColumn(ft.Text("Quantidade")),
                            ft.DataColumn(ft.Text("Valor Unitário")),
                            ft.DataColumn(ft.Text("Valor Total")),
                            ft.DataColumn(ft.Text("Tipo Venda")),
                        ],
                        rows=dataRows,
                        data_text_style= ft.TextStyle(
                            size=ft.TextThemeStyle.BODY_MEDIUM,
                            color=ft.Colors.BLACK,
                            font_family="Roboto Mono"
                        ),
                        heading_text_style= ft.TextStyle(
                            size=ft.TextThemeStyle.BODY_MEDIUM,
                            color=ft.Colors.BLACK,
                            font_family="Roboto Mono",
                            bgcolor=ft.Colors.BLUE_GREY_100
                        ),
                    )
                    msgProtheus = row['msg'] if not pd.isna(row['msg']) else " "
                    showMsg = ft.Text(
                        value=msgProtheus,
                        style=ft.TextStyle(
                            size=ft.TextThemeStyle.BODY_MEDIUM,
                            color=ft.Colors.RED if not row['sucess'] else ft.Colors.GREEN,
                            font_family="Roboto Mono"
                        )
                    )
                    expansion = ft.ExpansionTile(
                        controls=[itensTable, showMsg],
                        expand=True,
                        title=ft.Text(f"Itens do Pedido"),
                        trailing=ft.Icon(ft.Icons.ARROW_DROP_DOWN),
                        affinity=ft.TileAffinity.LEADING,
                        collapsed_bgcolor=ft.Colors.BLUE_GREY_50,
                        bgcolor=ft.Colors.BLUE_GREY_100,
                        text_color=ft.Colors.BLACK,
                        collapsed_text_color=ft.Colors.BLACK,
                        controls_padding=ft.padding.all(0)
                    )
                    conteudo.append(expansion)
                    conteudo.append(ft.Divider())
                id = str(row['id'])
        if page.views:
            page.views[0] = ft.View(
                "/",
                controls=conteudo,
                appbar=ft.AppBar(title=ft.Text("Pedidos de Venda"), bgcolor=ft.Colors.BLUE_100),
                scroll="auto"
            )
        else:
            page.views.append(
                ft.View(
                    "/",
                    controls=conteudo,
                    appbar=ft.AppBar(title=ft.Text("Pedidos de Venda"), bgcolor=ft.Colors.BLUE_100),
                    scroll="auto"
                )
            )
        page.update()

    def route_change(e):
        page.views.clear()
        if page.route == "/":
            build_home_view()
        elif page.route == "/neworder":
            page.views.append(
                ft.View(
                    "/neworder",
                    controls=neworder.get_insert_order_view(page),
                    appbar=ft.AppBar(title=ft.Text("Novo Pedido de Venda"), bgcolor=ft.Colors.BLUE_100),
                    scroll="auto"
                )
            )
        page.update()

    def view_pop(e):
        page.views.pop()
        page.update()

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)

if __name__ == "__main__":
    # Executa o aplicativo Flet em modo web:
    # ft.app(target=main, view=ft.WEB_BROWSER, port=8000, host="0.0.0.0")
    # Executa o aplicativo Flet em modo desktop:
    ft.app(target=main)
import pandas as pd
import os
import json

from rabbitMQ.message import get_message

def getOrders():
    """Função genérica para obter pedidos de um arquivo Excel.
    Retorna um DataFrame do Pandas contendo os pedidos.
    """
    dfOrders = pd.DataFrame()
    if os.path.exists("orders.xlsx"):
        dfOrders = pd.read_excel("orders.xlsx", 
                                    dtype={
                                        'id': str,
                                        'cliente_codigo': str,
                                        'cliente_loja': str,
                                        'cond_pagamento': str,
                                        'produto_codigo': str,
                                        'quantidade': float,
                                        'valor_unitario': float,
                                        'valor_total': float,
                                        'tipo_venda': str,
                                        'msg': str,
                                        'sucess': bool},
                                    parse_dates=['data'])
    return dfOrders


def refreshOrders():
    """Função para consultar a Fila do RabbitMQ e atualizar os pedidos.
    """    
   
    # Ler mensagens
    received_message = get_message(queue_name = 'pedidos_protheus')
    
    # Preparar dicionário para armazenar os pedidos
    pedidos_dict = [json.loads(msg) for msg in received_message]
    
    # Transformar em um DataFrame
    dfOrdersRefresh = pd.DataFrame(pedidos_dict)
    if dfOrdersRefresh.shape[0] == 0:
        print("Não foram encontradas mensagens na fila 'pedidos_protheus'.")
        return
    
    # Recuperar pedidos existentes
    dfOrders = getOrders()
    
    # Realizar o merge dos DataFrames
    dfOrdersRefresh.rename(columns={
        'msg': 'msg_refresh',
        'sucess': 'sucess_refresh',
        }, inplace=True)
    dfOrders = pd.merge(dfOrders, dfOrdersRefresh, on='id', how='left')
    
    # Atualizar 'msg' onde 'msg' é diferente de 'msg_refresh'
    dfOrders.loc[(dfOrders['msg'] != dfOrders['msg_refresh']) & (~dfOrders['msg_refresh'].isna()), 'msg'] = dfOrders['msg_refresh']
    # Atualizar 'sucess' onde 'sucess' é diferente de 'sucess_refresh'
    dfOrders.loc[(dfOrders['sucess'] != dfOrders['sucess_refresh']) & (~dfOrders['sucess_refresh'].isna()), 'sucess'] = dfOrders['sucess_refresh']
    
    # Remover as colunas de refresh
    dfOrders.drop(columns=['msg_refresh', 'sucess_refresh'], inplace=True)
    
    # Atualizar a "base de dados"
    dfOrders.to_excel("orders.xlsx", index=False)
    
    return 



if __name__ == "__main__":
    refreshOrders()
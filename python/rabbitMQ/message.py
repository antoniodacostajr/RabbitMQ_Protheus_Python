import pika

def insert_message(queue_name, message, host='localhost', port=5672, username='guest', password='guest'):
    """
    Envia uma mensagem para uma fila RabbitMQ local.

    :param queue_name: Nome da fila
    :param message: Mensagem a ser enviada (string)
    :param host: Host do RabbitMQ (padrão: localhost)
    :param port: Porta do RabbitMQ (padrão: 5672)
    :param username: Usuário do RabbitMQ (padrão: guest)
    :param password: Senha do RabbitMQ (padrão: guest)
    """
    credentials = pika.PlainCredentials(username, password)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=host, port=port, credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=message.encode('utf-8'),
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        )
    )
    connection.close()
    
    
def get_message(queue_name, host='localhost', port=5672, username='guest', password='guest'):
    """
    Lê todas as mensagens da fila RabbitMQ local.

    :param queue_name: Nome da fila
    :param host: Host do RabbitMQ (padrão: localhost)
    :param port: Porta do RabbitMQ (padrão: 5672)
    :param username: Usuário do RabbitMQ (padrão: guest)
    :param password: Senha do RabbitMQ (padrão: guest)
    :return: Lista de mensagens lidas da fila (strings)
    """
    credentials = pika.PlainCredentials(username, password)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=host, port=port, credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    messages = []
    while True:
        method_frame, header_frame, body = channel.basic_get(queue=queue_name, auto_ack=False)
        if method_frame:
            mensagem = body.decode('utf-8')
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            messages.append(mensagem)
        else:
            break
    connection.close()
    return messages
    
    

    
if __name__ == "__main__":
    # Exemplo de uso
    queue_name = 'pedidos_protheus'
    
    # Ler mensagem
    received_message = get_message(queue_name)
    print(f'Mensagem recebida: {received_message}')
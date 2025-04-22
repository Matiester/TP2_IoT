import asyncio, ssl, certifi, logging, os
import aiomqtt

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s:%(message)s', level=logging.INFO, datefmt='%d/%m/%Y %H:%M:%S %z')

async def multi_queue(client,colat1,colat2):
    async for message in client.messages:
        if message.topic.matches(os.environ['TOPICO1']):
            colat1.put_nowait(message)
        elif message.topic.matches(os.environ['TOPICO2']):
            colat2.put_nowait(message)

async def control_contador(client,contador):
    log = logging.getLogger("Contador")
    while True:
        contador["valor"]+=1
        await client.publish("CONTADOR", contador["valor"])
        log.info(f"Se ha incrementado el contador a: {contador['valor']}")
        await asyncio.sleep(3)

async def estado_servidor(client):
    log = logging.getLogger("Estado")
    while True:
        await client.publish("ESTADO", "Servidor: Activo")
        log.info("Informe de Estado Activo")
        await asyncio.sleep(5)


async def EscucharTopicos(client, cola_topico, topico):
    await client.subscribe(topico)
    log = logging.getLogger(topico)
    while True:
        message = await cola_topico.get()
        log.info(f"Mensaje del Tópico [{topico}]: {message.payload.decode()}")

async def main():
    contador = {"valor": 0} 
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True
    tls_context.load_default_certs()
    async with aiomqtt.Client(
        os.environ['SERVIDOR'],
        port=8883,
        tls_context=tls_context,
    ) as client:
        cola1 = asyncio.Queue()
        cola2 = asyncio.Queue()
        asyncio.create_task(control_contador(client, contador))
        asyncio.create_task(estado_servidor(client))
        asyncio.create_task(multi_queue(client,cola1,cola2))
        asyncio.create_task(EscucharTopicos(client,cola1, os.environ['TOPICO1']))
        asyncio.create_task(EscucharTopicos(client,cola2, os.environ['TOPICO2']))
        await asyncio.Event().wait()
            

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Apagando cliente MQTT")
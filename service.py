import asyncio
import websockets
import json
import os

class SignallingServer:
    def __init__(self, host="0.0.0.0", port=None):
        self.host = host
        self.port = port or os.environ.get('PORT', 1111)
        self.clients = {}
        self.first = ''
        self.second = ''

    async def register(self, websocket, member_id):
        self.clients[member_id] = websocket  
        if len(self.clients) == 1:
            self.first = member_id 
            print(f"new connection : {member_id} len: {len(self.clients)} first: {self.first}")
        
        if len(self.clients) == 2 and self.first != member_id:
            self.second = member_id
            print(f"new connection : {member_id} len: {len(self.clients)} first: {self.first} second: {self.second}")
            await self.send_message(self.first, "1" + str(member_id))
        else:
            await self.send_message(self.first, "0")

    async def unregister(self, member_id):
        if member_id in self.clients:
            del self.clients[member_id]
            print(f"client {member_id} removed")

    async def send_message(self, target_id, message):
        if target_id in self.clients:
            websocket = self.clients[target_id]
            await websocket.send(message)
        else:
            print(f"{target_id} not found")

    async def receive_message(self, websocket):
        message = await websocket.recv()
        data = json.loads(message)
        return data
    
    async def handle_message(self, member_id, message):
        data = json.loads(message)
        print(f"received message from {member_id}: {data}")
        
        target_id = data.get('target_id')
        if target_id:
            await self.send_message(target_id, message)

    async def handler(self, websocket, path):
        try:
            registration_data = await self.receive_message(websocket)
            member_id = registration_data['member_id']
            
            if len(self.clients) < 2:
                await self.register(websocket, member_id)
            else:
                print('enough users present')
                await websocket.close()

            async for message in websocket:
                await self.handle_message(member_id, message)
        except websockets.ConnectionClosed:
            print(f"Connection closed: {member_id}") 
        finally:
            await self.unregister(member_id)  

    async def start(self):
        server = await websockets.serve(self.handler, self.host, self.port)
        print(f"Signaling server started on ws://{self.host}:{self.port}")
        await server.wait_closed()  

def main():
    server = SignallingServer()
    asyncio.run(server.start())

if __name__ == "__main__":
    main()

import socket
import json
import time
from pymongo import MongoClient

# MongoDB connection
client = MongoClient('mongodb://your_mongodb_connection_string')
db = client['your_database_name']
collection = db['your_collection_name']

host = '192.168.50.222'
port = 12345
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host, port))
s.listen(1)

conn, addr = s.accept()
print('Connected by', addr)

while True:
    data = conn.recv(1024)
    data_decode = data.decode()
    vs = json.loads(data_decode)
    v1_air_quality_data = vs['v1']
    v2_gas_sensor_data = vs['v2']

    # Print received data
    print(data)

    # Sending response based on conditions
    if v1_air_quality_data <= 25 and v2_gas_sensor_data > 145:
        conn.sendall(b'Air Quality is Fine and there is no gas leakage')
        time.sleep(1)
    elif 25 < v1_air_quality_data and v2_gas_sensor_data < 145:
        conn.sendall(b'Air Quality is not Fine and there is a gas leakage')
        time.sleep(1)
    elif 25 < v1_air_quality_data and v2_gas_sensor_data > 145:
        conn.sendall(b'Air Quality is not Fine but there is no gas leakage')
        time.sleep(1)

    # Saving data to MongoDB
    data_to_insert = {
        'v1_air_quality_data': v1_air_quality_data,
        'v2_gas_sensor_data': v2_gas_sensor_data
    }
    collection.insert_one(data_to_insert)

# Close the connection
# conn.close()

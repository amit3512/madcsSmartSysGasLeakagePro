# echo_server.py
import socket
import json
import time
host = '192.168.50.222'        # Symbolic name meaning all available interfaces
port = 12345     # Arbitrary non-privileged port
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
 print(data)    
 if v1_air_quality_data <=25 and v2_gas_sensor_data > 145:
   conn.sendall(b'Air Quality is Fine and there is no gas leakage')    
   time.sleep(1)    
 elif 25 < v1_air_quality_data and v2_gas_sensor_data < 145 :
   conn.sendall(b'Air Quality is not Fine and there is a gas leakage')
   time.sleep(1)
 elif 25 < v1_air_quality_data and v2_gas_sensor_data > 145 :
   conn.sendall(b'Air Quality is not Fine but there is no gas leakage')
   time.sleep(1)    
#conn.close()


# include Python's socket library
from socket import *
from time import time, localtime, sleep

# create UDP socket
serverName = 'nasaserver'
serverPort = 21000
serverSocket = socket(AF_INET, SOCK_DGRAM)

# bind socket to local port number 12000
serverSocket.bind(('', serverPort))
print('The server is ready to receive')

#dictionary holding field's of Nasa's R.R. fields
nasaServerRR = {
  "R1": {
    "Record": 0,
    "Name": "www.nasa.gov", 
    "Type": "A",
    "Value" : "23.22.39.120",
    "TTL": None,
    "Static": 1
  },
  "R2": {
    "Record": 1,
    "Name": "ares.jsc.nasa.gov", 
    "Type": "A",
    "Value" : "192.68.197.15",
    "TTL": None,
    "Static": 1
  }
}


# loop forever

while 1:
  # Read from UDP socket into message, getting client's address (client IP and port)
  message, clientAddress = serverSocket.recvfrom(2048)
  modifiedMessage = message.decode()

  # Extract hostname and query type from the received query
  query_parts = modifiedMessage.split(',')
  q_transaction_id = query_parts[0]
  query_QR = query_parts[1]
  query_type = query_parts[2]
  q_name_len = query_parts[3]
  q_value_len = query_parts[4]
  hostname = query_parts[5]
  query_value = query_parts[6]

  print(f"DNS NASA Server: The server with address {clientAddress} sent a(n) {query_type} request for hostname \"{hostname}\"");

  key = None
  response = ""

  for record_key, record_value in nasaServerRR.items():
    # iterate through the viasatServerRR table, check if the name and type exist
    record_name = record_value["Name"]
    record_type = record_value["Type"]
    record_ip = record_value["Value"]
    # If record exists, make key = record_key
    if record_name == hostname and query_type == record_type:
      key = record_key
      # DNS response and the Value from RR table
      response = f"{q_transaction_id},{1},{record_type},{len(record_name)},{len(record_ip)},{record_name},{record_ip}"
      break
    else:
      print(f"DNS NASA Server: An {query_type} record for hostname {hostname} was not found")
      response = ""

  # Send the DNS response back to the local server
  serverSocket.sendto(response.encode(), clientAddress)
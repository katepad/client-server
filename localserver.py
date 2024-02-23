from socket import *
from time import time

# create UDP socket
serverName = 'localserver'
serverPort = 15000
serverSocket = socket(AF_INET, SOCK_DGRAM)

# bind socket to local port number 15000
serverSocket.bind(('', serverPort))
print('The server is ready to receive')

# Dictionary to store Local Server's RR Table
localServerRR = {
  "R1": {
    "Record": 0,
    "Name" : "www.vistausd.org",
    "Type": "A",
    "Value": "104.17.162.128",
    "TTL": None,
    "Static": 1
  },
  "R2": {
    "Record": 1,
    "Name": "rbv.vistausd.org",
    "Type": "A",
    "Value": "104.17.162.160",
    "TTL": None,
    "Static": 1
  },
  "R3": {
    "Record": 2,
    "Name": "rbv1.vistausd.org",
    "Type": "CNAME",
    "Value": "rbv.vistausd.org",
    "TTL": None,
    "Static": 1
  },
  "R4": {
    "Record": 3,
    "Name": "rbv1.vistausd.org",
    "Type": "A",
    "Value": "104.17.162.161",
    "TTL": None,
    "Static": 1
  },
  "R5": {
    "Record": 4,
    "Name": "vhs.vistausd.org",
    "Type": "A",
    "Value": "104.17.162.192",
    "TTL": None,
    "Static": 1
  },
  "R6": {
    "Record": 5,
    "Name": "nasa.gov",
    "Type": "NS",
    "Value": "dns.nasa.gov",
    "TTL": None,
    "Static": 1
  },
  "R7": {
    "Record": 6,
    "Name": "nsf.gov",
    "Type": "NS",
    "Value": "dns.nsf.gov",
    "TTL": None,
    "Static": 1
  }
}

servers = [
  ('nsf', 22000),
  ('nasa', 21000),
]

localServerRQ = {
}

transaction_id_2 = 1

# Loop forever
while True:
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


  # To store the information needed to send back to client
  key = None
  # To store the response taken from key that will be sent back to client
  response = ""
  record_name = None
  record_type = None
  record_ip = None
  
  for record_key, record_value in localServerRR.items():
    # iterate through the localServerRR table, check if the name and type exist
    record_name = record_value["Name"]
    record_type = record_value["Type"]
    record_ip = record_value["Value"]
    # If record exists, make key = record_key
    if record_name == hostname and query_type == record_type:
      key = record_key

      print(f"Client: An {record_type} record for hostname {record_name} is found in current RR. No need to ask other servers.")
      break
    else:
      print(f"DNS Local Server: Record for hostname was not found")

  #if no record found, ask other servers for their record.
  if key is None:
    # Iterate over the list of servers and try to get the record from each one
    for server_name, server_port in servers:
      # Construct a query to send to the server
      server_query = f"{transaction_id_2},{0},{query_type},{len(hostname)},{None},{hostname},{None}"

      print(f"Local DNS Server: storing query temporarily with transaction #{transaction_id_2} and type {query_type} until a response is given.")
      #store into temp query table
      localServerRQ["R"f"{len(localServerRQ)}"] = {
        "Transaction": q_transaction_id,
        "Type": query_type
      }

      serverSocket.sendto(server_query.encode(), ('localhost', server_port))
      print(f"Local DNS Server: I sent an {query_type} request to the local DNS server for the hostname \"{hostname}\"")
      # Receive the response from the server
      server_response, _ = serverSocket.recvfrom(2048)

      # Check if the response is not empty
      if server_response:

        # Parse the server response

        query_parts = server_response.decode().split(',')
        r_transaction_id = query_parts[0]
        response_qr = query_parts[1]
        server_type = query_parts[2]
        server_name_len = query_parts[3]
        server_val_len = query_parts[4]
        server_name = query_parts[5]
        server_value = query_parts[6]

        record_name = server_name
        record_type = server_type
        record_ip = server_value

        #check temp query table
        for rq_key, rq_value in localServerRQ.items():
          rq_transaction = rq_value["Transaction"]
          rq_type = rq_value["Type"]
          if rq_transaction == r_transaction_id and rq_type == server_type:
            localServerRQ.pop(rq_key)
            break

        print(f"Local DNS Server: storing hostname \"{server_name}\" with IP address {server_value} and type {server_type}")
        
        # Add the server response to the local server's RR table
        localServerRR["R"f"{len(localServerRR)}"] = {
            "Record": len(localServerRR),
            "Name": server_name,
            "Type": server_type,
            "Value": server_value,
            "TTL": float(time()) + 60,
            "Static": 0
        }
        key = "R"f"{len(localServerRR)}"
        
      else:
        print("Local DNS Server: record was not found")

  transaction_id_2 = transaction_id_2 + 1

  #  Update time. Take out expired TTLs
  keys_to_remove = []

  current_time = float(time())

  for key in list(localServerRR.keys()):
    record_value = localServerRR[key]
    if record_value["Static"] == 0:
        start_time = record_value["TTL"]
        elapsed_time = current_time - start_time
        remaining_ttl = record_value["TTL"] - elapsed_time
        # Update the TTL value in the original dictionary
        localServerRR[key]["TTL"] = remaining_ttl
        # Check and delete records with TTL reached zero
        if remaining_ttl <= 0:
          keys_to_remove.append(key)  # Append key to remove later

  # Remove expired records
  for key in keys_to_remove:
    localServerRR.pop(key, None)

  
  print("\nRR Table for localserver:")
  for record_key, record_value in localServerRR.items():
    print(f"{record_key}:")
    for key, value in record_value.items():
        print(f"  {key}: {value}")
    print()
  
  #response given back to client
  response = f"{q_transaction_id},{1},{record_type},{len({record_name})},{len({record_ip})},{record_name},{record_ip}"

  # Send the DNS response back to the client

  if response:
    serverSocket.sendto(response.encode(), clientAddress)

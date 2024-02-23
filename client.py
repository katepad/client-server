# include Python's socket library
from socket import *
from time import time, localtime, sleep

#defining the RR table structure on the client side

clientName = 'localhost'

#create UDP socket for sever
clientSocket = socket(AF_INET, SOCK_DGRAM)

# Dictionary to store Local Server's RR Table
clientRR = {
}

#Dictionary to store temp query requests
clientRQ = {
}

transaction_id = 0

while 1:
  #get user keyboard input
  message1 = input('(1) Enter the host name/domain name:')
  message2 = input('(2) Enter the type of DNS query:')
  #length of message
  message1_length = len(message1)

  #make a key and set it to none
  key = None

  if message1 == "" or message2 == "":
    print(f"Client: An {message2} record for hostname {message1} was not found")
    clientSocket.close()
    quit()

  for record_key, record_value in clientRR.items():
    # iterate through the clientRR table, check if the name and type exist
    record_name = record_value["Name"]
    record_type = record_value["Type"]
    record_ip = record_value["Value"]
    # If record exists, make key = record_key
    if record_name == message1 and record_type == message2:
      key = record_key
      print(f"Client: An {message2} record for hostname {message1} is found in current RR. No need to ask local server.")
      break
    else:
      print(f"Client: Record for hostname was not found")

  if key is None:
    # building a query
    main_msg = f"{transaction_id},{0},{message2},{message1_length},{None},{message1},{None}"

    print(f"Client: storing query temporarily with transaction #{transaction_id} and type {message2} until a response is given.")
    #store into temp query table
    clientRQ["R"f"{len(clientRQ)}"] = {
      "Transaction": transaction_id,
      "Type": message2
    }
  
    # Attach server name, port to message; send into socket 
    clientSocket.sendto(main_msg.encode(),('localhost', 15000))

    print(f"Client: I sent an {message2} request to the local DNS server for the hostname \"{message1}\"")
  
    # read reply characters from socket into string 
    modifiedMessage, serverAddress = clientSocket.recvfrom(2048)
  
    # check if modifiedMessage is not empty before printing
    if modifiedMessage:
      # print out received string
      #print(modifiedMessage.decode())
  
      response_message = modifiedMessage.decode()
  
      #parse response
      query_parts = response_message.split(',')
      r_transaction_id = query_parts[0]
      response_qr = query_parts[1]
      server_type = query_parts[2]
      server_name_len = query_parts[3]
      server_val_len = query_parts[4]
      server_name = query_parts[5]
      server_value = query_parts[6]

      print(f"Client: The server with IP address {server_value} sent a(n) {server_type} request for hostname \"{server_name}\"");

      print(f"Client: Taking out query from temporary table with transaction #{transaction_id} and type {message2}")
      #check temp query table
      for rq_key, rq_value in clientRQ.items():
        rq_transaction = rq_value["Transaction"]
        rq_type = rq_value["Type"]
        if rq_transaction == r_transaction_id and rq_type == server_type:
          clientRQ.pop(rq_key)
          break

      print(f"Client: storing hostname \"{server_name}\" with IP address {server_value} and type {server_type}")
      #then store it into its RR table with new TTL
      clientRR["R"f"{len(clientRR)}"] = {
          "Record": len(clientRR),
          "Name": server_name,
          "Type": server_type,
          "Value": server_value,
          "TTL": float(time()) + 60,
          "Static": 0
      }
  
      #update transaction id
      transaction_id = transaction_id + 1

      print(f'{server_value}')
  
    else:
      print(f"Client: An {message2} record for hostname {message1} was not found")


  # Update time. Take out  TTLs
  keys_to_remove = []

  current_time = float(time())

  for key in list(clientRR.keys()):
    record_value = clientRR[key]
    if record_value["Static"] == 0:
        start_time = record_value["TTL"]
        elapsed_time = current_time - start_time
        remaining_ttl = record_value["TTL"] - elapsed_time
        # Update the TTL value in the original dictionary
        clientRR[key]["TTL"] = remaining_ttl
        # Check and delete records with TTL reached zero
        if remaining_ttl <= 0:
            keys_to_remove.append(key)  # Append key to remove later

  # Remove expired records
  for key in keys_to_remove:
    clientRR.pop(key, None)  
      
  print("\nRR Table for client:")
  for record_key, record_value in clientRR.items():
    print(f"{record_key}:")
    for key, value in record_value.items():
        print(f"  {key}: {value}")
    print()

clientSocket.close()

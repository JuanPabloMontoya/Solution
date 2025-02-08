import veryfi

client_id = 'vrfhjAs5kPIee2Yvy7F0osVV5MX6zXKFTriJyLS'
client_secret = 'NJoXZcE25MBxv97merROYW5CvYBJLmNwrGDoYEWzv970T0fyeE2pxAXlP93huX46Bf1NbgM6jGzVb3LzSrTWZYDEGcyaruHwfWAr75EfA87rcoo29NLYzWRWJdogbc1N'
username = 'juanpamon.13'
api_key = 'f604ee697fd73c0ba1bb99a536bcde0b'

client = veryfi.Client(client_id, client_secret, username, api_key)

#categories = 

json_result = client.process_document(r'Documents\synth-switch_v5-4.pdf')

print(json_result)


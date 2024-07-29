import secrets

secret_key = secrets.token_hex(16)  # Generates a 32-character hexadecimal string
print(secret_key)


from flask import Flask

app = Flask(__name__)
app.secret_key = '6f64c4e71bf4f967ae9a85c281291083'



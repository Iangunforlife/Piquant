from cryptography.fernet import Fernet

message = input("Enter your message:")

key = Fernet.generate_key()

fernet = Fernet(key)

em = fernet.encrypt(message.encode())

print("original message: ", message)
print("encrypted message: ", em)

dm = fernet.decrypt(em).decode()

print("decrypted message: ", dm)

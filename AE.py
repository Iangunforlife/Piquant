import rsa

publicKey, privateKey = rsa.newkeys(512)

message = input("Enter your message:")

em = rsa.encrypt(message.encode(),publicKey)

print("original string: ", message)
print("encrypted string: ", em)

dm = rsa.decrypt(em, privateKey).decode()

print("decrypted string: ", dm)

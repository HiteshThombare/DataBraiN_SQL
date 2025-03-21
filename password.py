import pymysql
import bcrypt

db_user = "root"
db_password = "root"
db_host = "localhost"
db_name = "hitesh"

connection = pymysql.connect(host=db_host, user=db_user, password=db_password, database=db_name)
cursor = connection.cursor()

username = "Hitesh"
plain_password = "1912"

# Hash the password before storing
hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

query = "INSERT INTO users (username, password) VALUES (%s, %s)"
cursor.execute(query, (username, hashed_password))
connection.commit()

cursor.close()
connection.close()
print("✅ User created successfully!")

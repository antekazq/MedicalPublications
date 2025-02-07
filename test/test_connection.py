import os 
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.database import get_connection, close_connection

try:
    conn = get_connection()
    print("Connection succeeded")
    close_connection(conn)
except Exception as e:
    print("Error occured", e)

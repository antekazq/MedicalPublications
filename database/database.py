import psycopg2
import os
from dotenv import load_dotenv

#Get the variables from the .env file
load_dotenv()

#Get connection to the PostgreSQL database
def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),  
        port=os.getenv("DB_PORT", "5432")  
    )

#Close connection to database
def close_connection(conn):
    if conn:
        conn.close()

#Insert a journal into the database if it doesn't already exist
def insert_journal(journal_name):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        #Check if journal already exists
        cursor.execute("SELECT journal_id FROM journals WHERE name = %s;", (journal_name,))
        result = cursor.fetchone()

        if result:
            print(f"Tidskriften '{journal_name}' finns redan i databasen.")
            return result[0]  
        
        #Insert new journal
        cursor.execute("""
            INSERT INTO journals (name)
            VALUES (%s)
            RETURNING journal_id;
        """, (journal_name,))

        journal_id = cursor.fetchone()[0]
        conn.commit()
        print(f"Tidskriften '{journal_name}' har sparats i databasen med ID {journal_id}.")
        return journal_id

    except Exception as e:
        print(f"Fel vid sparande av tidskrift i databasen: {e}")
        conn.rollback()

    finally:
        cursor.close()
        close_connection(conn)

#Insert a publication into the database if it doesn't already exist
def insert_publication(pub_date, title, abstract, journal_id, doi):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        #Check if the publication already exists based on DOI
        cursor.execute("SELECT * FROM publications WHERE doi = %s;", (doi,))
        if cursor.fetchone():
            print(f"Publikationen med DOI {doi} finns redan i databasen.")
            return

        #Insert new publication
        cursor.execute("""
            INSERT INTO publications (publication_date, title, abstract, journal_id, doi)
            VALUES (%s, %s, %s, %s, %s);
        """, (pub_date, title, abstract, journal_id, doi))

        conn.commit()
        print(f"Publikationen {title} har sparats i databasen.")
    
    except Exception as e:
        print(f"Fel vid sparande i databasen: {e}")
        conn.rollback()
    
    finally:
        cursor.close()
        close_connection(conn)

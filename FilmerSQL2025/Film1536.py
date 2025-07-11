import pyodbc
import openai
import json
from typing import List, Optional
import time
import os
from dotenv import load_dotenv

# Last inn .env filen
load_dotenv()

class FilmEmbeddingProcessor1536D:
    def __init__(self, connection_string: str, openai_api_key: str):
        self.connection_string = connection_string
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        
    def get_films_without_vectors(self) -> List[tuple]:
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                query = """
                SELECT FilmID, Film, Beskrivelse 
                FROM [dbo].[Filmer] 
                WHERE VektorBeskrivelse IS NULL
                """
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            print(f"Feil ved henting av filmer: {e}")
            return []
    
    def generate_embedding(self, text: str, model: str = "text-embedding-3-small") -> Optional[List[float]]:
        try:
            response = self.openai_client.embeddings.create(
                model=model,
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Feil ved generering av embedding: {e}")
            return None
    
    def update_film_vector(self, film_id: int, vector: List[float]) -> bool:
        """
        Oppdaterer VektorBeskrivelse for en film - robust metode
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                
                # Metode 1: Bruk stored procedure med VARCHAR(MAX)
                try:
                    # Opprett JSON string
                    vector_json = json.dumps(vector)
                    
                    # Bruk stored procedure eller direkte SQL med VARCHAR(MAX)
                    query = """
                    DECLARE @JsonVector VARCHAR(MAX) = ?;
                    UPDATE [dbo].[Filmer] 
                    SET VektorBeskrivelse = CAST(@JsonVector AS VECTOR(1536))
                    WHERE FilmID = ?;
                    """
                    
                    cursor.execute(query, (vector_json, film_id))
                    conn.commit()
                    return True
                    
                except Exception as e1:
                    print(f"Metode 1 feilet for FilmID {film_id}: {e1}")
                    
                    # Metode 2: Bruk JSON_ARRAY funksjonen
                    try:
                        # Opprett parameter-liste for JSON_ARRAY
                        params = vector + [film_id]
                        placeholders = ", ".join(["?" for _ in vector])
                        
                        query = f"""
                        UPDATE [dbo].[Filmer] 
                        SET VektorBeskrivelse = JSON_ARRAY({placeholders})
                        WHERE FilmID = ?
                        """
                        
                        cursor.execute(query, params)
                        conn.commit()
                        print(f"✓ JSON_ARRAY metode fungerte for FilmID {film_id}")
                        return True
                        
                    except Exception as e2:
                        print(f"Metode 2 feilet for FilmID {film_id}: {e2}")
                        
                        # Metode 3: Bruk bulk insert via temp table
                        try:
                            # Opprett temp table og bulk insert
                            temp_table = f"##TempVector_{film_id}"
                            
                            # Opprett temp table
                            cursor.execute(f"""
                            CREATE TABLE {temp_table} (
                                FilmID INT,
                                VectorData VARCHAR(MAX)
                            )
                            """)
                            
                            # Insert data
                            vector_json = json.dumps(vector)
                            cursor.execute(f"""
                            INSERT INTO {temp_table} (FilmID, VectorData)
                            VALUES (?, ?)
                            """, (film_id, vector_json))
                            
                            # Update hovedtabell
                            cursor.execute(f"""
                            UPDATE f
                            SET VektorBeskrivelse = CAST(t.VectorData AS VECTOR(1536))
                            FROM [dbo].[Filmer] f
                            INNER JOIN {temp_table} t ON f.FilmID = t.FilmID
                            """)
                            
                            # Dropp temp table
                            cursor.execute(f"DROP TABLE {temp_table}")
                            
                            conn.commit()
                            print(f"✓ Temp table metode fungerte for FilmID {film_id}")
                            return True
                            
                        except Exception as e3:
                            print(f"Alle metoder feilet for FilmID {film_id}: {e3}")
                            return False
                            
        except Exception as e:
            print(f"Connection feil for FilmID {film_id}: {e}")
            return False
    
    def process_all_films(self, delay_seconds: float = 1.0):
        films = self.get_films_without_vectors()
        
        if not films:
            print("Ingen filmer funnet som mangler vektorer.")
            return
        
        print(f"Fant {len(films)} filmer som trenger 1536D vektorer...")
        
        for film_id, film_title, description in films:
            print(f"\nProsesserer: {film_title}")
            
            # Generer embedding
            embedding = self.generate_embedding(description)
            if embedding is None:
                print(f"Kunne ikke generere embedding for {film_title}")
                continue
            
            print(f"Generert 1536D vektor (lengde: {len(embedding)})")
            
            # Oppdater database
            if self.update_film_vector(film_id, embedding):
                print(f"✓ Oppdatert 1536D vektor for {film_title}")
            else:
                print(f"✗ Feil ved oppdatering av {film_title}")
            
            time.sleep(delay_seconds)
        
        print("\n=== Prosessering av filmer fullført med 1536 dimensjoner ===")

def main():
    CONNECTION_STRING = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=TH\\SQL2025;"
        "Database=VectorDB;"
        "Trusted_Connection=yes;"
    )
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    if not OPENAI_API_KEY:
        print("Feil: OPENAI_API_KEY ikke funnet i .env fil")
        return
    
    processor = FilmEmbeddingProcessor1536D(CONNECTION_STRING, OPENAI_API_KEY)
    processor.process_all_films(delay_seconds=1.0)

if __name__ == "__main__":
    main()
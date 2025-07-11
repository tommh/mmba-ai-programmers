import pyodbc
import openai
import json
from typing import List, Optional
import time
import os
from dotenv import load_dotenv

# Last inn .env filen
load_dotenv()

class SporsmalEmbeddingProcessor1536D:
    def __init__(self, connection_string: str, openai_api_key: str):
        self.connection_string = connection_string
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        
    def get_questions_without_vectors(self) -> List[tuple]:
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                query = """
                SELECT SporsmalID, Sporsmal 
                FROM [dbo].[Sporsmal] 
                WHERE VektorSporsmal IS NULL
                """
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            print(f"Feil ved henting av spørsmål: {e}")
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
    
    def update_question_vector(self, sporsmal_id: int, vector: List[float]) -> bool:
        """
        Oppdaterer VektorSporsmal for et spørsmål - robust metode
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
                    UPDATE [dbo].[Sporsmal] 
                    SET VektorSporsmal = CAST(@JsonVector AS VECTOR(1536))
                    WHERE SporsmalID = ?;
                    """
                    
                    cursor.execute(query, (vector_json, sporsmal_id))
                    conn.commit()
                    return True
                    
                except Exception as e1:
                    print(f"Metode 1 feilet for SporsmalID {sporsmal_id}: {e1}")
                    
                    # Metode 2: Bruk JSON_ARRAY funksjonen
                    try:
                        # Opprett parameter-liste for JSON_ARRAY
                        params = vector + [sporsmal_id]
                        placeholders = ", ".join(["?" for _ in vector])
                        
                        query = f"""
                        UPDATE [dbo].[Sporsmal] 
                        SET VektorSporsmal = JSON_ARRAY({placeholders})
                        WHERE SporsmalID = ?
                        """
                        
                        cursor.execute(query, params)
                        conn.commit()
                        print(f"✓ JSON_ARRAY metode fungerte for SporsmalID {sporsmal_id}")
                        return True
                        
                    except Exception as e2:
                        print(f"Metode 2 feilet for SporsmalID {sporsmal_id}: {e2}")
                        
                        # Metode 3: Bruk bulk insert via temp table
                        try:
                            # Opprett temp table og bulk insert
                            temp_table = f"##TempVectorSporsmal_{sporsmal_id}"
                            
                            # Opprett temp table
                            cursor.execute(f"""
                            CREATE TABLE {temp_table} (
                                SporsmalID INT,
                                VectorData VARCHAR(MAX)
                            )
                            """)
                            
                            # Insert data
                            vector_json = json.dumps(vector)
                            cursor.execute(f"""
                            INSERT INTO {temp_table} (SporsmalID, VectorData)
                            VALUES (?, ?)
                            """, (sporsmal_id, vector_json))
                            
                            # Update hovedtabell
                            cursor.execute(f"""
                            UPDATE s
                            SET VektorSporsmal = CAST(t.VectorData AS VECTOR(1536))
                            FROM [dbo].[Sporsmal] s
                            INNER JOIN {temp_table} t ON s.SporsmalID = t.SporsmalID
                            """)
                            
                            # Dropp temp table
                            cursor.execute(f"DROP TABLE {temp_table}")
                            
                            conn.commit()
                            print(f"✓ Temp table metode fungerte for SporsmalID {sporsmal_id}")
                            return True
                            
                        except Exception as e3:
                            print(f"Alle metoder feilet for SporsmalID {sporsmal_id}: {e3}")
                            return False
                            
        except Exception as e:
            print(f"Connection feil for SporsmalID {sporsmal_id}: {e}")
            return False
    
    def process_all_questions(self, delay_seconds: float = 1.0):
        questions = self.get_questions_without_vectors()
        
        if not questions:
            print("Ingen spørsmål funnet som mangler vektorer.")
            return
        
        print(f"Fant {len(questions)} spørsmål som trenger 1536D vektorer...")
        
        for sporsmal_id, sporsmal_text in questions:
            print(f"\nProsesserer: {sporsmal_text}")
            
            # Generer embedding
            embedding = self.generate_embedding(sporsmal_text)
            if embedding is None:
                print(f"Kunne ikke generere embedding for spørsmål ID {sporsmal_id}")
                continue
            
            print(f"Generert 1536D vektor (lengde: {len(embedding)})")
            
            # Oppdater database
            if self.update_question_vector(sporsmal_id, embedding):
                print(f"✓ Oppdatert 1536D vektor for spørsmål ID {sporsmal_id}")
            else:
                print(f"✗ Feil ved oppdatering av spørsmål ID {sporsmal_id}")
            
            time.sleep(delay_seconds)
        
        print("\n=== Prosessering av spørsmål fullført med 1536 dimensjoner ===")
    
    def show_questions_status(self):
        """
        Viser status på alle spørsmål i databasen
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                
                # Hent statistikk
                cursor.execute("""
                SELECT 
                    COUNT(*) as TotaltSporsmal,
                    SUM(CASE WHEN VektorSporsmal IS NULL THEN 1 ELSE 0 END) as ManglerVektorer,
                    SUM(CASE WHEN VektorSporsmal IS NOT NULL THEN 1 ELSE 0 END) as HarVektorer
                FROM [dbo].[Sporsmal]
                """)
                
                stats = cursor.fetchone()
                total, missing, has_vectors = stats
                
                print(f"\n📊 STATUS SPØRSMÅL (1536D):")
                print(f"   Totalt spørsmål: {total}")
                print(f"   Har vektorer: {has_vectors}")
                print(f"   Mangler vektorer: {missing}")
                
                # Vis spørsmål som mangler vektorer
                if missing > 0:
                    cursor.execute("""
                    SELECT SporsmalID, Sporsmal 
                    FROM [dbo].[Sporsmal] 
                    WHERE VektorSporsmal IS NULL
                    ORDER BY SporsmalID
                    """)
                    
                    missing_questions = cursor.fetchall()
                    print(f"\n❌ Spørsmål som mangler vektorer:")
                    for qid, qtext in missing_questions:
                        print(f"   ID {qid}: {qtext}")
                
                # Vis sample av spørsmål som har vektorer
                if has_vectors > 0:
                    cursor.execute("""
                    SELECT TOP 3 SporsmalID, Sporsmal,
                           CASE 
                               WHEN VektorSporsmal IS NOT NULL THEN 
                                   SUBSTRING(CAST(VektorSporsmal AS VARCHAR(MAX)), 1, 50) + '...'
                               ELSE 'NULL'
                           END as VektorSample,
                           CASE 
                               WHEN VektorSporsmal IS NOT NULL THEN 
                                   LEN(CAST(VektorSporsmal AS VARCHAR(MAX)))
                               ELSE 0
                           END as VektorLengde
                    FROM [dbo].[Sporsmal] 
                    WHERE VektorSporsmal IS NOT NULL
                    ORDER BY SporsmalID
                    """)
                    
                    sample_questions = cursor.fetchall()
                    print(f"\n✅ Sample av spørsmål som har vektorer:")
                    for qid, qtext, vsample, vlength in sample_questions:
                        print(f"   ID {qid}: {qtext}")
                        print(f"           Vektor: {vsample}")
                        print(f"           Lengde: {vlength} tegn")
                        print()
                
        except Exception as e:
            print(f"Feil ved henting av status: {e}")

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
    
    processor = SporsmalEmbeddingProcessor1536D(CONNECTION_STRING, OPENAI_API_KEY)
    
    # Vis status før prosessering
    processor.show_questions_status()
    
    # Prosesser alle spørsmål med 1536 dimensjoner
    processor.process_all_questions(delay_seconds=1.0)
    
    # Vis status etter prosessering
    print("\n" + "="*50)
    processor.show_questions_status()

if __name__ == "__main__":
    main()
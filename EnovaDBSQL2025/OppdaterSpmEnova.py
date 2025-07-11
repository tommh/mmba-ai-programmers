import pyodbc
import openai
import json
import numpy as np
from typing import List, Optional
import time
import os
from dotenv import load_dotenv

# Last inn .env filen
load_dotenv()

class SporsmalEmbeddingProcessor:
    def __init__(self, connection_string: str, openai_api_key: str):
        """
        Initialiserer prosessoren med database og OpenAI konfiguration
        
        Args:
            connection_string: SQL Server connection string
            openai_api_key: OpenAI API nøkkel
        """
        self.connection_string = connection_string
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        
    def get_records_without_vectors(self) -> List[tuple]:
        """
        Henter alle spørsmål som mangler vektorer
        
        Returns:
            Liste med (SpmID, Sporsmal) tupler
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                query = """
                SELECT [SpmID], [Sporsmal]
                FROM [Enova].[ev_enova].[Sporsmal]
                WHERE [Vector] IS NULL
                """
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            print(f"Feil ved henting av records: {e}")
            return []
    
    def generate_embedding(self, text: str, model: str = "text-embedding-3-small") -> Optional[List[float]]:
        """
        Genererer embedding for gitt tekst via OpenAI API
        
        Args:
            text: Tekst som skal konverteres til embedding
            model: OpenAI embedding modell
            
        Returns:
            Liste med float verdier (embedding) eller None ved feil
        """
        try:
            # Håndter None eller tom tekst
            if not text or text.strip() == "":
                print("Tom eller None tekst - hopper over")
                return None
                
            response = self.openai_client.embeddings.create(
                model=model,
                input=text.strip(),
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Feil ved generering av embedding: {e}")
            return None
    
    def format_vector_for_sql_server(self, embedding: List[float]) -> str:
        """
        Formaterer embedding for SQL Server vector(1536) format
        
        Args:
            embedding: Original embedding (1536 dimensjoner)
            
        Returns:
            Formatert string for SQL Server
        """
        # Konverter til komma-separert string omsluttet av firkantparenteser
        vector_values = ','.join(map(str, embedding))
        return f"[{vector_values}]"
    
    def update_record_vector(self, spm_id: int, embedding: List[float]) -> bool:
        """
        Oppdaterer Vector for en spørsmål record
        
        Args:
            spm_id: SpmID til recorden
            embedding: Full embedding (1536 dimensjoner)
            
        Returns:
            True hvis vellykket, False ellers
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                
                # Konverter embedding til SQL Server vector(1536) format
                vector_str = self.format_vector_for_sql_server(embedding)
                
                # Bruk parameterized query med eksplisitt varchar casting
                query = """
                DECLARE @vector_data VARCHAR(MAX) = ?
                UPDATE [Enova].[ev_enova].[Sporsmal] 
                SET [Vector] = CAST(@vector_data AS vector(1536)),
                    [OppdatertDato] = GETDATE()
                WHERE [SpmID] = ?
                """
                
                cursor.execute(query, (vector_str, spm_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Feil ved oppdatering av vektor for SpmID {spm_id}: {e}")
            return False
    
    def process_all_records(self, delay_seconds: float = 1.0):
        """
        Prosesserer alle spørsmål som mangler vektorer
        
        Args:
            delay_seconds: Pause mellom API kall for å unngå rate limiting
        """
        records = self.get_records_without_vectors()
        
        if not records:
            print("Ingen spørsmål funnet som mangler vektorer.")
            return
        
        print(f"Fant {len(records)} spørsmål som trenger vektorer...")
        
        success_count = 0
        error_count = 0
        
        for spm_id, sporsmal in records:
            print(f"\nProsesserer: SpmID={spm_id}")
            print(f"Spørsmål: {sporsmal[:100]}..." if len(sporsmal) > 100 else f"Spørsmål: {sporsmal}")
            
            # Sjekk om tekst er tilgjengelig
            if not sporsmal or sporsmal.strip() == "":
                print(f"Tom tekst for SpmID {spm_id} - hopper over")
                error_count += 1
                continue
            
            # Generer embedding
            embedding = self.generate_embedding(sporsmal)
            if embedding is None:
                print(f"Kunne ikke generere embedding for SpmID {spm_id}")
                error_count += 1
                continue
            
            # Verifiser at vi har riktig antall dimensjoner
            if len(embedding) != 1536:
                print(f"Uventet embedding størrelse: {len(embedding)} (forventet 1536)")
                error_count += 1
                continue
            
            # Oppdater database med full embedding
            if self.update_record_vector(spm_id, embedding):
                print(f"✓ Oppdatert vector for SpmID {spm_id} (1536 dimensjoner)")
                success_count += 1
            else:
                print(f"✗ Feil ved oppdatering av SpmID {spm_id}")
                error_count += 1
            
            # Pause for å unngå rate limiting
            time.sleep(delay_seconds)
        
        print(f"\n=== Prosessering fullført ===")
        print(f"Vellykkede oppdateringer: {success_count}")
        print(f"Feil: {error_count}")
        print(f"Totalt prosessert: {success_count + error_count}")

def main():
    # Konfiguration
    CONNECTION_STRING = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=TH\\SQL2025;"
        "Database=Enova;"
        "Trusted_Connection=yes;"
    )
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Les fra .env fil
    
    if not OPENAI_API_KEY:
        print("Feil: OPENAI_API_KEY ikke funnet i .env fil")
        return
    
    # Opprett prosessor
    processor = SporsmalEmbeddingProcessor(CONNECTION_STRING, OPENAI_API_KEY)
    
    # Prosesser alle records
    processor.process_all_records(delay_seconds=1.0)

if __name__ == "__main__":
    main()

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

class EnovaEmbeddingProcessor:
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
        Henter alle records som mangler vektorer
        
        Returns:
            Liste med (attestid, attestnummer, EnovaVectorTextInput) tupler
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                query = """
                SELECT EI.attestid, EI.attestnummer, v.[EnovaVectorTextInput] 
                FROM [Enova].[ev_enova].[Version1] v
                INNER JOIN [ev_enova].[EstateInfo] EI ON EI.attestnummer = v.attestnummer
                WHERE EI.[EnovaVector] IS NULL
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
    
    def update_record_vector(self, attestid: int, attestnummer: str, embedding: List[float]) -> bool:
        """
        Oppdaterer EnovaVector for en record
        
        Args:
            attestid: ID til recorden
            attestnummer: Attestnummer (alternativ nøkkel)
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
                UPDATE [ev_enova].[EstateInfo] 
                SET [EnovaVector] = CAST(@vector_data AS vector(1536))
                WHERE attestid = ?
                """
                
                cursor.execute(query, (vector_str, attestid))
                
                # Sjekk om oppdateringen påvirket noen rader
                if cursor.rowcount == 0:
                    # Prøv med attestnummer hvis attestid ikke ga resultater
                    query_alt = """
                    DECLARE @vector_data VARCHAR(MAX) = ?
                    UPDATE [ev_enova].[EstateInfo] 
                    SET [EnovaVector] = CAST(@vector_data AS vector(1536))
                    WHERE attestnummer = ?
                    """
                    cursor.execute(query_alt, (vector_str, attestnummer))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Feil ved oppdatering av vektor for attestid {attestid}/attestnummer {attestnummer}: {e}")
            return False
    
    def process_all_records(self, delay_seconds: float = 1.0):
        """
        Prosesserer alle records som mangler vektorer
        
        Args:
            delay_seconds: Pause mellom API kall for å unngå rate limiting
        """
        records = self.get_records_without_vectors()
        
        if not records:
            print("Ingen records funnet som mangler vektorer.")
            return
        
        print(f"Fant {len(records)} records som trenger vektorer...")
        
        success_count = 0
        error_count = 0
        
        for attestid, attestnummer, text_input in records:
            print(f"\nProsesserer: attestid={attestid}, attestnummer={attestnummer}")
            
            # Sjekk om tekst er tilgjengelig
            if not text_input or text_input.strip() == "":
                print(f"Tom tekst for attestnummer {attestnummer} - hopper over")
                error_count += 1
                continue
            
            # Generer embedding
            embedding = self.generate_embedding(text_input)
            if embedding is None:
                print(f"Kunne ikke generere embedding for attestnummer {attestnummer}")
                error_count += 1
                continue
            
            # Verifiser at vi har riktig antall dimensjoner
            if len(embedding) != 1536:
                print(f"Uventet embedding størrelse: {len(embedding)} (forventet 1536)")
                error_count += 1
                continue
            
            # Oppdater database med full embedding
            if self.update_record_vector(attestid, attestnummer, embedding):
                print(f"✓ Oppdatert vektor for attestnummer {attestnummer} (1536 dimensjoner)")
                success_count += 1
            else:
                print(f"✗ Feil ved oppdatering av attestnummer {attestnummer}")
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
    processor = EnovaEmbeddingProcessor(CONNECTION_STRING, OPENAI_API_KEY)
    
    # Prosesser alle records
    processor.process_all_records(delay_seconds=1.0)

if __name__ == "__main__":
    main()
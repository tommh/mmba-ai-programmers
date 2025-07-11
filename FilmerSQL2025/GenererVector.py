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

class FilmEmbeddingProcessor:
    def __init__(self, connection_string: str, openai_api_key: str):
        """
        Initialiserer prosessoren med database og OpenAI konfiguration
        
        Args:
            connection_string: SQL Server connection string
            openai_api_key: OpenAI API nøkkel
        """
        self.connection_string = connection_string
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        
    def get_films_without_vectors(self) -> List[tuple]:
        """
        Henter alle filmer som mangler vektorer
        
        Returns:
            Liste med (FilmID, Film, Beskrivelse) tupler
        """
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
        """
        Genererer embedding for gitt tekst via OpenAI API
        
        Args:
            text: Tekst som skal konverteres til embedding
            model: OpenAI embedding modell
            
        Returns:
            Liste med float verdier (embedding) eller None ved feil
        """
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
    
    def reduce_dimensions(self, embedding: List[float], target_dim: int = 2) -> List[float]:
        """
        Reduserer dimensjonene til embeddings (for SQL Server vector(2))
        Bruker PCA-lignende tilnærming
        
        Args:
            embedding: Original embedding
            target_dim: Mål dimensjon (2 for vector(2))
            
        Returns:
            Redusert embedding
        """
        if len(embedding) <= target_dim:
            return embedding[:target_dim]
        
        # Enkel dimensjons-reduksjon: ta de første komponentene og normaliser
        arr = np.array(embedding)
        
        # Ta første to komponenter
        reduced = arr[:target_dim]
        
        # Normaliser til [-1, 1] range
        if np.max(np.abs(reduced)) > 0:
            reduced = reduced / np.max(np.abs(reduced))
        
        return reduced.tolist()
    
    def update_film_vector(self, film_id: int, vector: List[float]) -> bool:
        """
        Oppdaterer VektorBeskrivelse for en film
        
        Args:
            film_id: ID til filmen
            vector: Vector som skal lagres
            
        Returns:
            True hvis vellykket, False ellers
        """
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                
                # Konverter vector til SQL Server format
                vector_str = f"[{vector[0]}, {vector[1]}]"
                
                query = """
                UPDATE [dbo].[Filmer] 
                SET VektorBeskrivelse = ? 
                WHERE FilmID = ?
                """
                cursor.execute(query, (vector_str, film_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Feil ved oppdatering av vektor for FilmID {film_id}: {e}")
            return False
    
    def process_all_films(self, delay_seconds: float = 1.0):
        """
        Prosesserer alle filmer som mangler vektorer
        
        Args:
            delay_seconds: Pause mellom API kall for å unngå rate limiting
        """
        films = self.get_films_without_vectors()
        
        if not films:
            print("Ingen filmer funnet som mangler vektorer.")
            return
        
        print(f"Fant {len(films)} filmer som trenger vektorer...")
        
        for film_id, film_title, description in films:
            print(f"\nProsesserer: {film_title}")
            
            # Generer embedding
            embedding = self.generate_embedding(description)
            if embedding is None:
                print(f"Kunne ikke generere embedding for {film_title}")
                continue
            
            # Reduser dimensjoner til 2D
            vector_2d = self.reduce_dimensions(embedding, 2)
            
            # Oppdater database
            if self.update_film_vector(film_id, vector_2d):
                print(f"✓ Oppdatert vektor for {film_title}: {vector_2d}")
            else:
                print(f"✗ Feil ved oppdatering av {film_title}")
            
            # Pause for å unngå rate limiting
            time.sleep(delay_seconds)
        
        print("\n=== Prosessering fullført ===")

def main():
    # Konfiguration
    CONNECTION_STRING = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=TH\\SQL2025;"  # Din SQL Server instans
        "Database=VectorDB;"   # Din database
        "Trusted_Connection=yes;"  # Windows Authentication
    )
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Les fra .env fil
    
    if not OPENAI_API_KEY:
        print("Feil: OPENAI_API_KEY ikke funnet i .env fil")
        return
    
    # Opprett prosessor
    processor = FilmEmbeddingProcessor(CONNECTION_STRING, OPENAI_API_KEY)
    
    # Prosesser alle filmer
    processor.process_all_films(delay_seconds=1.0)

if __name__ == "__main__":
    main()
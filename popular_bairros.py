import sqlite3
from modulos.database import criar_table
import uuid
from geopy.geocoders import Nominatim
import time

conn = sqlite3.connect("Banco_dados.db")
cursor = conn.cursor()
cursor.execute("DELETE FROM Bairros")

criar_table()
geolocator = Nominatim(user_agent="coord_slz")
def popular():

    try:
        with open('bairros_slz.txt', 'r', encoding='utf-8') as b:
            bairros = [linha.strip() for linha in b if linha.strip()]
    except FileNotFoundError: 
        print('Arquivo não encontrado')
        return
    
    bairros_inserir = []

    nomes_bairros = set(bairros)

    for bairro in nomes_bairros:

        busca_bairro =  f"{bairro}, São Luis, MA, Brasil"
        local = geolocator.geocode(busca_bairro, timeout=10)

        if local:
            lat = local.latitude
            lon = local.longitude
        else:
            lat = -2.5307
            lon = -44.3068

        id_bairro = str(uuid.uuid4())
        bairros_inserir.append((id_bairro, bairro, lat, lon))

        time.sleep(1)
    
    cursor.executemany('''

        INSERT OR IGNORE INTO Bairros (uuid_bairro, nome_bairro, latitude, longitude)
        VALUES (?, ?, ?, ?)

        ''', bairros_inserir)

    conn.commit()
    print(f"Sucesso! {cursor.rowcount} novos Bairros foram inseridos/verificados.")
    conn.close()

popular()
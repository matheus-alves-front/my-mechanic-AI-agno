import asyncio
import aiohttp
import json
import os
import logging
import tldextract
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import trafilatura
from datetime import datetime

# --- CONFIGURAÇÕES ---
MAX_DEPTH = 2  # Profundidade (2 é seguro para teste, aumente para 3 ou 4 depois)
MAX_CONCURRENT_REQUESTS = 5 # Comece baixo para não tomar Block IP
OUTPUT_DIR = "dataset_mecanica_full"
MIN_CONTENT_LENGTH = 300 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RecursiveMechanicCrawler:
    def __init__(self):
        self.visited = set()
        self.queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

    def is_valid_url(self, url, base_domain):
        parsed = urlparse(url)
        ext = tldextract.extract(url)
        domain = f"{ext.domain}.{ext.suffix}"
        
        invalid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.css', '.js', '.mp4')
        if url.lower().endswith(invalid_extensions):
            return False
            
        return base_domain in domain and url not in self.visited

    def save_content(self, url, content, metadata):
        # Cria um hash simples ou timestamp para o nome do arquivo não sobrescrever
        safe_name = tldextract.extract(url).domain
        filename = f"{safe_name}_{datetime.now().strftime('%H%M%S_%f')}.jsonl"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        entry = {
            "url": url,
            "title": metadata.title if metadata else "No Title",
            "content": content, # O texto puro
            "scraped_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    async def process_url(self, session, url, current_depth, base_domain):
        if current_depth > MAX_DEPTH:
            return

        async with self.semaphore:
            try:
                logging.info(f"Processando (Depth {current_depth}): {url}")
                async with session.get(url, timeout=20) as response:
                    if response.status != 200:
                        logging.warning(f"Erro {response.status}: {url}")
                        return
                    # Tenta detectar encoding, fallback para utf-8
                    html = await response.text(encoding='utf-8', errors='ignore')
            except Exception as e:
                logging.error(f"Falha ao conectar {url}: {e}")
                return

        # Extração
        content = trafilatura.extract(html, include_comments=False, include_tables=True)
        metadata = trafilatura.extract_metadata(html)

        if content and len(content) > MIN_CONTENT_LENGTH:
            self.save_content(url, content, metadata)

        # Recursividade
        if current_depth < MAX_DEPTH:
            soup = BeautifulSoup(html, 'html.parser')
            for link in soup.find_all('a', href=True):
                absolute_url = urljoin(url, link['href'])
                absolute_url = absolute_url.split('#')[0].split('?')[0] # Limpa URL
                
                if self.is_valid_url(absolute_url, base_domain):
                    if absolute_url not in self.visited:
                        self.visited.add(absolute_url)
                        self.queue.put_nowait((absolute_url, current_depth + 1, base_domain))

    async def worker(self, session):
        while True:
            try:
                # Timeout de 5s para esperar novos itens na fila. Se vazio, encerra.
                url, depth, base_domain = await asyncio.wait_for(self.queue.get(), timeout=5.0)
            except asyncio.TimeoutError:
                break
            except asyncio.QueueEmpty:
                break
            
            await self.process_url(session, url, depth, base_domain)
            self.queue.task_done()

    async def run(self, seed_urls):
        async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) MechanicBot/1.0'}) as session:
            for url in seed_urls:
                ext = tldextract.extract(url)
                base_domain = f"{ext.domain}.{ext.suffix}"
                self.queue.put_nowait((url, 0, base_domain))
                self.visited.add(url)

            workers = [asyncio.create_task(self.worker(session)) for _ in range(MAX_CONCURRENT_REQUESTS)]
            await asyncio.gather(*workers)

# --- LISTAS DE ALVOS ---
if __name__ == "__main__":
    
    # 1. Diagnóstico (OBD-II)
    diagnostico = [
        "https://www.obd-codes.com/trouble_codes/",
        "https://www.troublecodes.net/",
        "https://www.suaoficina.com.br/tabela-codigos-obd2",
    ]

    # 2. Mecânica Técnica (How-To)
    tecnica = [
        "https://auto.howstuffworks.com/car-parts-roundup.htm",
        "https://autopapo.uol.com.br/manutencao/",
        "https://quatrorodas.abril.com.br/auto-servico/",
        "https://www.carbibles.com/",
    ]

    # 3. Manuais e Peças
    manuais = [
        "https://www.2carpros.com/articles",
        "https://repairpal.com/encyclopedia",
    ]

    # Juntando tudo
    MASTER_LIST = [
        "https://www.obd-codes.com/trouble_codes/",
        "https://doutorcarro.com.br/",
        "https://www.obd-codes.com/trouble_codes/", # A Bíblia dos códigos em inglês
        "https://www.troublecodes.net/", # Focado em diagnóstico técnico
        "https://www.engine-codes.com/", # Ótimo para diagramas de motor e sintomas
        "https://www.autocodes.com/", # Base gigantesca de códigos específicos por montadora
        "https://pt.wikipedia.org/wiki/OBD-II", # Contexto geral
        "https://www.suaoficina.com.br/tabela-codigos-obd2",
        "https://auto.howstuffworks.com/car-parts-roundup.htm", # Explicações profundas de como funciona
        "https://www.aa1car.com/library.htm", # Biblioteca técnica MASSIVA (Visual feio, conteúdo ouro)
        "https://www.flatout.com.br/category/tecnica/", # PT-BR, altíssimo nível técnico (Project Cars, etc)
        "https://quatrorodas.abril.com.br/auto-servico/", # Testes e mecânica PT-BR
        "https://www.carbibles.com/", # Guias e revisões técnicas
        "https://www.freeasestudyguides.com/", # Guias de estudo para certificação ASE (Mecânico PRO)
        "https://axleaddict.com/auto-repair/",
        "https://forum.oficinaonline.com.br/", # Comunidade BR forte
        "https://www.clubedohardware.com.br/forum/92-carros-e-motos-eletrônica-embarcada-e-mecânica/", # Sim, eles têm área de carros
        "https://www.pistonheads.com/gassing/forum.asp?h=0&f=23&mid=0", # Fórum técnico UK (muito bom)
        "https://bobistheoilguy.com/forums/",
    ]

    print(f"Iniciando Scraper com {len(MASTER_LIST)} URLs raiz...")
    print("Pressione CTRL+C para parar forçadamente se precisar.")
    
    crawler = RecursiveMechanicCrawler()
    try:
        asyncio.run(crawler.run(MASTER_LIST))
    except KeyboardInterrupt:
        print("\nScraper interrompido pelo usuário.")

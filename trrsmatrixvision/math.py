import os
import PyPDF2
import unidecode
import re

# Diretório onde o script está sendo executado
pasta_raiz = os.getcwd()

def extrair_texto_pdf(caminho_pdf):
    try:
        with open(caminho_pdf, 'rb') as arquivo:
            leitor = PyPDF2.PdfReader(arquivo)
            # Tenta extrair texto das 3 primeiras páginas
            for i in range(min(3, len(leitor.pages))):
                texto = leitor.pages[i].extract_text()
                if texto:
                    linha = texto.strip().split('\n')[0]
                    if linha:
                        return linha
    except Exception as e:
        print(f'❌ Erro ao extrair texto de {caminho_pdf}: {e}')
    return None

def limpar_nome_arquivo(nome):
    # Remove caracteres inválidos para nomes de arquivos
    nome = unidecode.unidecode(nome)
    nome = re.sub(r'[\\/*?:"<>|]', '', nome)
    nome = nome.replace(' ', '_')
    return nome[:50]

def mover_para_subpasta(raiz, nome_pasta, nome_arquivo, caminho_antigo):
    pasta_destino = os.path.join(raiz, nome_pasta)
    os.makedirs(pasta_destino, exist_ok=True)
    caminho_novo = os.path.join(pasta_destino, nome_arquivo)
    contador = 1
    while os.path.exists(caminho_novo):
        nome_arquivo_base, ext = os.path.splitext(nome_arquivo)
        caminho_novo = os.path.join(pasta_destino, f"{nome_arquivo_base}_{contador}{ext}")
        contador += 1
    os.rename(caminho_antigo, caminho_novo)
    return caminho_novo

for raiz, subpastas, arquivos in os.walk(pasta_raiz):
    for arquivo in arquivos:
        if arquivo.lower().endswith('.pdf'):
            caminho_antigo = os.path.join(raiz, arquivo)
            # Ignora arquivos já renomeados
            if re.match(r'^[\w\-]{1,50}\.pdf$', arquivo):
                continue
            titulo = extrair_texto_pdf(caminho_antigo)
            if titulo:
                titulo_limpo = limpar_nome_arquivo(titulo)
                novo_nome = f'{titulo_limpo}.pdf'
                try:
                    caminho_novo = mover_para_subpasta(raiz, titulo_limpo, novo_nome, caminho_antigo)
                    print(f'✔️ Movido e renomeado: {caminho_antigo} -> {caminho_novo}')
                except Exception as e:
                    print(f'❌ Erro ao mover/renomear {arquivo}: {e}')
            else:
                print(f'❓ Texto não encontrado em: {arquivo}')
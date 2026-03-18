#!/usr/bin/env python3
"""
add_knowledge.py — Alimenta a base de conhecimento do CardioRisk Chat

Uso:
  # Listar o que já existe:
  python add_knowledge.py --list

  # Adicionar PDF local:
  python add_knowledge.py artigo.pdf

  # Adicionar vários PDFs de uma vez:
  python add_knowledge.py artigo1.pdf artigo2.pdf diretriz.pdf

  # Buscar artigo do PubMed Central por ID:
  python add_knowledge.py --pmc PMC10153050 PMC11676592 PMC9876543

  # Combinado:
  python add_knowledge.py meu_artigo.pdf --pmc PMC12345678
"""

import argparse
import json
import re
import sys
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"

# Tamanho alvo de cada chunk (em caracteres). Chunks menores = mais precisão na busca;
# chunks maiores = menos overhead de contexto. 700-900 é um bom equilíbrio.
CHUNK_SIZE = 800
CHUNK_MIN = 80  # descartar chunks muito pequenos (cabeçalhos, números de página, etc.)


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str) -> list[str]:
    """
    Divide o texto em chunks de CHUNK_SIZE caracteres, respeitando parágrafos.
    Quando um único parágrafo excede o limite, divide por sentenças.
    """
    paragraphs = [p.strip() for p in re.split(r'\n{2,}|\r\n{2,}', text) if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= CHUNK_SIZE:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            if len(para) > CHUNK_SIZE:
                # Parágrafo longo: dividir por sentenças
                sentences = re.split(r'(?<=[.!?])\s+', para)
                buf = ""
                for sent in sentences:
                    if len(buf) + len(sent) + 1 <= CHUNK_SIZE:
                        buf = (buf + " " + sent).strip()
                    else:
                        if buf:
                            chunks.append(buf)
                        # Sentença sozinha maior que CHUNK_SIZE: forçar quebra
                        if len(sent) > CHUNK_SIZE:
                            for i in range(0, len(sent), CHUNK_SIZE):
                                chunks.append(sent[i:i + CHUNK_SIZE])
                            buf = ""
                        else:
                            buf = sent
                current = buf
            else:
                current = para

    if current:
        chunks.append(current)

    return [c for c in chunks if len(c) >= CHUNK_MIN]


# ---------------------------------------------------------------------------
# PDF (PyMuPDF)
# ---------------------------------------------------------------------------

def extract_pdf(path: Path) -> tuple[str, list[dict]]:
    """
    Extrai texto de um PDF página a página e gera chunks.
    Retorna (título, [{page, text}, ...]) — mesmo formato do sbc2024.json.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("Erro: PyMuPDF não instalado. Execute: pip install pymupdf")
        sys.exit(1)

    doc = fitz.open(str(path))

    # Tenta obter título dos metadados
    title = (doc.metadata.get("title") or "").strip()
    if not title or len(title) < 4:
        title = path.stem

    result: list[dict] = []
    for page_num, page in enumerate(doc, 1):
        raw = page.get_text("text")
        if not raw or not raw.strip():
            continue
        # Limpa ruídos comuns de PDFs (hifenização, espaços duplos)
        cleaned = re.sub(r'(\w)-\n(\w)', r'\1\2', raw)  # desfaz hifenização
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        for chunk in chunk_text(cleaned):
            result.append({"page": page_num, "text": chunk})

    doc.close()
    print(f"  {len(doc)} páginas → {len(result)} chunks")
    return title, result


# ---------------------------------------------------------------------------
# PubMed Central
# ---------------------------------------------------------------------------

def fetch_pmc(pmc_id: str) -> tuple[str, list[str]]:
    """
    Baixa um artigo do PubMed Central via API BioC e retorna (título, [chunks]).
    Retorna no formato dict {title, chunks} — mesmo formato dos artigos existentes.
    """
    import requests

    clean = pmc_id.upper().replace("PMC", "")
    url = (
        "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi"
        f"/BioC_json/PMC{clean}/unicode"
    )
    print(f"  Buscando PMC{clean} em PubMed Central...")
    resp = requests.get(url, timeout=30)

    if resp.status_code == 404:
        raise RuntimeError(f"Artigo PMC{clean} não encontrado (404). Verifique o ID.")
    resp.raise_for_status()

    data = resp.json()
    title = ""
    passages: list[str] = []

    for doc in data.get("documents", []):
        for passage in doc.get("passages", []):
            ptype = passage.get("infons", {}).get("type", "")
            section = passage.get("infons", {}).get("section_type", "").upper()
            text = passage.get("text", "").strip()

            if not text or len(text) < 30:
                continue
            if ptype == "title":
                title = text
                continue
            # Ignora seção de referências bibliográficas
            if section in ("REF", "REFERENCES", "ACKNOWLEDGMENTS", "ACKNOWLEDGE"):
                continue
            passages.append(text)

    combined = "\n\n".join(passages)
    chunks = chunk_text(combined)
    print(f"  {len(passages)} seções → {len(chunks)} chunks")
    return title or f"PMC{clean}", chunks


# ---------------------------------------------------------------------------
# Persistência
# ---------------------------------------------------------------------------

def _unique_path(base: Path) -> Path:
    """Garante que não sobrescreve um arquivo existente — adiciona sufixo _2, _3..."""
    if not base.exists():
        return base
    i = 2
    while True:
        candidate = base.with_stem(f"{base.stem}_{i}")
        if not candidate.exists():
            return candidate
        i += 1


def save_pdf(path: Path, chunks: list[dict]) -> Path:
    stem = re.sub(r'[^\w\-]', '_', path.stem.lower())[:40]
    out = _unique_path(KNOWLEDGE_DIR / f"{stem}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    return out


def save_article(filename: str, title: str, chunks: list[str]) -> Path:
    out = _unique_path(KNOWLEDGE_DIR / f"{filename}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"title": title, "chunks": chunks}, f, ensure_ascii=False, indent=2)
    return out


# ---------------------------------------------------------------------------
# Listagem
# ---------------------------------------------------------------------------

def list_knowledge():
    files = sorted(KNOWLEDGE_DIR.glob("*.json"))
    if not files:
        print("Base de conhecimento vazia.")
        return
    total = 0
    print(f"\n{'Arquivo':<38} {'Chunks':>6}  Título")
    print("-" * 80)
    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                n, t = len(data), f.stem
            else:
                n, t = len(data.get("chunks", [])), data.get("title", f.stem)
            total += n
            print(f"  {f.name:<36} {n:>6}  {t[:55]}")
        except Exception as e:
            print(f"  {f.name:<36}  ERRO: {e}")
    print("-" * 80)
    print(f"  {'TOTAL':<36} {total:>6}  ({len(files)} arquivos)\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Alimenta a base de conhecimento do CardioRisk Chat",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("files", nargs="*", help="Arquivos PDF para processar")
    parser.add_argument(
        "--pmc", nargs="+", metavar="ID",
        help="IDs de artigos do PubMed Central (ex: PMC10153050 ou só 10153050)"
    )
    parser.add_argument(
        "--list", "-l", action="store_true",
        help="Lista os arquivos na base de conhecimento e sai"
    )
    args = parser.parse_args()

    KNOWLEDGE_DIR.mkdir(exist_ok=True)

    if args.list or (not args.files and not args.pmc):
        list_knowledge()
        if not args.list:
            parser.print_help()
        return

    # --- PDFs ---
    for fp in (args.files or []):
        path = Path(fp)
        if not path.exists():
            print(f"\n[ERRO] Arquivo não encontrado: {fp}")
            continue
        if path.suffix.lower() != ".pdf":
            print(f"\n[AVISO] Ignorando (não é PDF): {fp}")
            continue
        print(f"\nProcessando PDF: {path.name}")
        try:
            title, chunks = extract_pdf(path)
            if not chunks:
                print("  Nenhum texto extraído — PDF pode estar em imagem/escaneado.")
                continue
            out = save_pdf(path, chunks)
            print(f"  ✔ Salvo: {out.name}  ({len(chunks)} chunks)  —  {title[:60]}")
        except Exception as e:
            print(f"  [ERRO] {e}")

    # --- Artigos PMC ---
    for pmc_id in (args.pmc or []):
        clean = pmc_id.upper().replace("PMC", "")
        filename = f"pmc{clean}"
        existing = KNOWLEDGE_DIR / f"{filename}.json"
        if existing.exists():
            print(f"\n[AVISO] {filename}.json já existe — use --list para ver. Ignorando.")
            continue
        print(f"\nBaixando artigo: PMC{clean}")
        try:
            title, chunks = fetch_pmc(clean)
            if not chunks:
                print("  Nenhum conteúdo extraído.")
                continue
            out = save_article(filename, title, chunks)
            print(f"  ✔ Salvo: {out.name}  ({len(chunks)} chunks)  —  {title[:60]}")
        except Exception as e:
            print(f"  [ERRO] {e}")

    print("\nBase de conhecimento atualizada.")
    print("Reinicie o backend para carregar os novos artigos: uvicorn main:app --reload")


if __name__ == "__main__":
    main()

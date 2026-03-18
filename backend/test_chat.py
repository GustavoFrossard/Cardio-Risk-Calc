"""
Teste automatizado do chat_service com casos clínicos conhecidos.
Verifica se o modelo responde corretamente aos casos da diretriz SBC 2024.

Uso:
    cd backend
    python test_chat.py
"""

import sys
import re
from dotenv import load_dotenv
load_dotenv()

from chat_service import chat

# ─── Cores ANSI ───────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# ─── Casos de teste ───────────────────────────────────────────────────────────

CASES = [
    {
        "name": "Colecistectomia + AVC + DM insulina (esperado: RCRI 3pts, Classe IV, 15%)",
        "messages": [
            {
                "role": "user",
                "content": (
                    "Paciente de 67 anos, portadora de HAS e DM tipo 2, com antecedente de "
                    "AVC isquêmico há 2 anos, em tratamento com insulinoterapia, AAS e "
                    "sinvastatina. Em programação de colecistectomia laparoscópica. "
                    "Calcule o RCRI."
                ),
            }
        ],
        "expect": {
            # O modelo deve mencionar exatamente 3 pontos
            "score": 3,
            # Classe IV
            "class": "iv",
            # 15%
            "pct": "15",
            # AVC deve ser mapeado como cerebrovascular (C4), NÃO como DAC (C2)
            "c4_present": True,
            "c2_absent": True,
            # C1 presente (colecistectomia = intraperitoneal)
            "c1_present": True,
            # C5 presente (insulina)
            "c5_present": True,
        },
    },
    {
        "name": "Cirurgia de baixo risco, sem comorbidades (esperado: RCRI 0pts, Classe I, 3.9%)",
        "messages": [
            {
                "role": "user",
                "content": (
                    "Paciente de 45 anos, sem comorbidades conhecidas, sem medicamentos. "
                    "Vai fazer uma cirurgia de catarata (ocular). Calcule o RCRI."
                ),
            }
        ],
        "expect": {
            "score": 0,
            "class": "i",
            "pct": "3",
            # C1 ausente (cirurgia ocular não é intraperitoneal/intratorácica)
            "c1_absent": True,
        },
    },
    {
        "name": "Cirurgia vascular (esperado: VSG-CRI, não RCRI)",
        "messages": [
            {
                "role": "user",
                "content": (
                    "Paciente de 72 anos com DAC, tabagista, DPOC leve. "
                    "Programado para revascularização periférica aberta por isquemia de MMII. "
                    "Qual índice usar e qual o risco?"
                ),
            }
        ],
        "expect": {
            # Deve usar VSG-CRI e não RCRI
            "index_vsg": True,
        },
    },
    {
        "name": "AVC não deve ser contado como DAC (erro clássico do modelo)",
        "messages": [
            {
                "role": "user",
                "content": (
                    "Paciente com histórico de AVC isquêmico. Vai fazer gastrectomia. "
                    "C2 do RCRI (doença isquêmica cardíaca) está presente?"
                ),
            }
        ],
        "expect": {
            # C2 deve estar AUSENTE — AVC é C4, não C2
            # (pergunta direta: o modelo pode responder apenas "❌ Ausente")
            "c2_absent": True,
        },
    },
]

# ─── Funções de verificação ───────────────────────────────────────────────────

def _norm(text: str) -> str:
    return text.lower()


def check_score(text: str, expected_score: int) -> tuple[bool, str]:
    """Verifica se o score esperado aparece no texto."""
    t = _norm(text)
    patterns = [
        rf"\b{expected_score}\s*ponto",
        rf"pontuação.*?{expected_score}",
        rf"total.*?{expected_score}",
        rf"score.*?{expected_score}",
        rf"rcri.*?{expected_score}",
        rf"{expected_score}.*?ponto",
    ]
    for p in patterns:
        if re.search(p, t):
            return True, f"score {expected_score} encontrado"
    return False, f"score {expected_score} NÃO encontrado"


def check_class(text: str, expected_class: str) -> tuple[bool, str]:
    t = _norm(text)
    patterns = [
        rf"classe\s+{expected_class}",
        rf"class\s+{expected_class}",
        rf"(classe|class)\s*(iii|ii|iv|i)".replace("(iii|ii|iv|i)", expected_class),
    ]
    for p in patterns:
        if re.search(p, t):
            return True, f"Classe {expected_class.upper()} encontrada"
    return False, f"Classe {expected_class.upper()} NÃO encontrada"


def check_pct(text: str, pct: str) -> tuple[bool, str]:
    t = _norm(text)
    if re.search(rf"{pct}[,.]?\d*\s*%", t) or re.search(rf"{pct}\s*%", t):
        return True, f"{pct}% encontrado"
    return False, f"{pct}% NÃO encontrado"


def check_c1_present(text: str) -> tuple[bool, str]:
    t = _norm(text)
    has_c1 = (
        ("c1" in t or "intraperitoneal" in t or "intratorácic" in t)
        and ("sim" in t or "✅" in t or "presente" in t or "conta" in t)
    )
    return has_c1, "C1 presente [OK]" if has_c1 else "C1 presente NAO confirmado"


def check_c1_absent(text: str) -> tuple[bool, str]:
    t = _norm(text)
    # For low-risk surgeries, C1 should be marked absent or model shouldn't assign it
    has_c1_absent = re.search(r"c1.{0,80}(não|nao|ausente|❌)", t) or \
                    re.search(r"(não|nao).{0,40}intraperitoneal", t) or \
                    re.search(r"cirurgia.{0,60}(baixo risco|não conta|nao conta)", t)
    return bool(has_c1_absent), "C1 ausente [OK]" if has_c1_absent else "C1 ausente NAO confirmado"


def check_c2_absent(text: str) -> tuple[bool, str]:
    t = _norm(text)
    # The model must NOT say C2 is PRESENT because of AVC.
    # A correct response has "❌ ausente" or "❌ não" in C2's verdict column.
    # We check: does "c2" row have an explicit PRESENT verdict citing AVC?
    # Pattern: C2 header → within 120 chars → (✅ or "presente" or "sim") → within 120 chars → "avc"
    c2_wrongly_present = re.search(
        r"c2.{0,80}(✅\s*presente|✅\s*sim\b).{0,120}avc",
        t
    )
    if c2_wrongly_present:
        return False, "C2 INCORRETAMENTE marcado como presente por AVC [FAIL]"
    # Check that C2 verdict is absent
    c2_absent = re.search(r"c2.{0,80}(❌\s*(ausente|não|nao)\b)", t) or \
                re.search(r"(doença isquêmica cardíaca|isquêmica cardíaca).{0,80}(❌|ausente|não\s+há)", t) or \
                re.search(r"(ausente|❌).{0,60}(sem dac|sem angina|avc não conta|avc nao conta)", t)
    # Also accept short "❌ ausente" as the full answer (direct question format)
    c2_short_absent = bool(re.match(r"\s*❌\s*(ausente|não)\s*$", t.strip()))
    ok = bool(c2_absent) or c2_short_absent
    return ok, "C2 corretamente ausente [OK]" if ok else "C2: resultado ambiguo (verificar manualmente)"


def check_c4_present(text: str) -> tuple[bool, str]:
    t = _norm(text)
    has_c4 = re.search(
        r"(c4|cerebrovascular|avc|acidente vascular).{0,100}(sim|✅|presente|conta|isquêmico)",
        t
    )
    return has_c4, "C4 (cerebrovascular) presente [OK]" if has_c4 else "C4 presente NAO confirmado"


def check_c5_present(text: str) -> tuple[bool, str]:
    t = _norm(text)
    has_c5 = re.search(
        r"(c5|insulino|insulina|diabetes).{0,80}(sim|✅|presente|conta)",
        t
    )
    return has_c5, "C5 (insulina) presente [OK]" if has_c5 else "C5 presente NAO confirmado"


def check_index_vsg(text: str) -> tuple[bool, str]:
    t = _norm(text)
    has_vsg = "vsg" in t or "vsg-cri" in t or "vascular surgery group" in t
    return has_vsg, "VSG-CRI mencionado [OK]" if has_vsg else "VSG-CRI NAO mencionado"


CHECKERS = {
    "score":      check_score,
    "class":      check_class,
    "pct":        check_pct,
    "c1_present": lambda t, _=None: check_c1_present(t),
    "c1_absent":  lambda t, _=None: check_c1_absent(t),
    "c2_absent":  lambda t, _=None: check_c2_absent(t),
    "c4_present": lambda t, _=None: check_c4_present(t),
    "c5_present": lambda t, _=None: check_c5_present(t),
    "index_vsg":  lambda t, _=None: check_index_vsg(t),
}

# ─── Runner ───────────────────────────────────────────────────────────────────

def run_case(case: dict) -> tuple[int, int]:
    """Run one test case. Returns (passed, total) assertion counts."""
    print(f"\n{BOLD}{CYAN}{'-'*70}{RESET}")
    print(f"{BOLD}CASO: {case['name']}{RESET}")
    print(f"{CYAN}{'-'*70}{RESET}")

    print(f"\n{YELLOW}>> Enviando ao modelo...{RESET}")
    try:
        response = chat(case["messages"])
    except Exception as e:
        print(f"{RED}ERRO ao chamar chat(): {e}{RESET}")
        return 0, len(case["expect"])

    print(f"\n{BOLD}Resposta do modelo:{RESET}")
    print(f"{response}\n")

    passed = 0
    total = 0
    for key, expected in case["expect"].items():
        checker = CHECKERS.get(key)
        if checker is None:
            continue
        total += 1
        if key in ("score", "class", "pct"):
            ok, msg = checker(response, expected)
        else:
            ok, msg = checker(response)

        symbol = f"{GREEN}[PASS]{RESET}" if ok else f"{RED}[FAIL]{RESET}"
        print(f"  {symbol}  {msg}")
        if ok:
            passed += 1

    return passed, total


def main():
    print(f"\n{BOLD}{'='*70}")
    print("  CardioRisk Chat - Testes de Qualidade do Modelo")
    print(f"{'='*70}{RESET}\n")

    total_passed = 0
    total_checks = 0

    for case in CASES:
        p, t = run_case(case)
        total_passed += p
        total_checks += t

    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    color = GREEN if total_passed == total_checks else (YELLOW if total_passed >= total_checks * 0.7 else RED)
    print(f"{BOLD}{color}RESULTADO FINAL: {total_passed}/{total_checks} verificacoes passaram{RESET}")
    if total_passed < total_checks:
        print(f"{YELLOW}[!] Verificacoes ambiguas podem precisar de revisao manual.{RESET}")
    print(f"{CYAN}{'='*70}{RESET}\n")

    sys.exit(0 if total_passed == total_checks else 1)


if __name__ == "__main__":
    main()

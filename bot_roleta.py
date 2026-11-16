import argparse
import json
import os
import time
from datetime import datetime

from roleta_bau import ELEMENTOS, PREMIOS, PREMIOS_RARIDADE, SAVE, fmt, rng

GIROS_PADRAO = 14_000
PASTA = os.path.dirname(os.path.abspath(__file__))
ARQ_ITENS = os.path.join(PASTA, "bot_itens.json")
ARQ_RELATORIO = os.path.join(PASTA, "bot_relatorio.txt")
NOMES = {p["id"]: p["nome"] for p in PREMIOS}


def sortear_detalhe(pid):
    if pid == "acessorio":
        return rng.choice(["picareta", "mochila"])
    if pid == "elemental":
        return rng.choice(list(ELEMENTOS))
    return None


def rodar(giros):
    contagem = {p["id"]: 0 for p in PREMIOS}
    itens = []
    randint = rng.randint
    for n in range(1, giros + 1):
        # mesma regra da roleta: do mais raro ao mais comum, um prêmio por giro
        for p in PREMIOS_RARIDADE:
            if randint(1, p["chance"]) == 1:
                contagem[p["id"]] += 1
                itens.append({"giro": n, "id": p["id"], "premio": p["nome"],
                              "detalhe": sortear_detalhe(p["id"])})
                break
    return contagem, itens


def ler_json(caminho, padrao):
    try:
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
        return dados if isinstance(dados, dict) else padrao
    except (OSError, ValueError):
        return padrao


def salvar_roleta(giros, contagem):
    dados = ler_json(SAVE, {})
    premios = dados.get("premios", {})
    dados["tentativas"] = int(dados.get("tentativas", 0)) + giros
    dados["premios"] = {p["id"]: int(premios.get(p["id"], 0)) + contagem[p["id"]] for p in PREMIOS}
    with open(SAVE, "w", encoding="utf-8") as f:
        json.dump(dados, f)


def salvar_itens(giros, itens, segundos):
    dados = ler_json(ARQ_ITENS, {"execucoes": []})
    dados.setdefault("execucoes", []).append({
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "giros": giros,
        "segundos": round(segundos, 3),
        "total_itens": len(itens),
        "itens": itens,
    })
    with open(ARQ_ITENS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)


def montar_relatorio(giros, contagem, itens, segundos):
    linhas = [f"RELATÓRIO DO BOT - {datetime.now():%d/%m/%Y %H:%M:%S}",
              f"Giros: {fmt(giros)}   |   Tempo: {segundos:.2f}s   |   "
              f"Itens ganhos: {fmt(len(itens))}", "",
              f"{'Prêmio':<22}{'Chance':>14}{'Esperado':>10}{'Ganhou':>8}", "-" * 54]
    for p in PREMIOS_RARIDADE:
        esperado = giros / p["chance"]
        linhas.append(f"{p['nome']:<22}{'1 em ' + fmt(p['chance']):>14}"
                      f"{esperado:>10.1f}{contagem[p['id']]:>8}")

    extras = {}
    for it in itens:
        if it["detalhe"]:
            extras.setdefault(it["id"], {}).setdefault(it["detalhe"], 0)
            extras[it["id"]][it["detalhe"]] += 1
    if extras:
        linhas += ["", "Detalhes:"]
        for pid, d in extras.items():
            linhas.append(f"  {NOMES[pid]}: " + ", ".join(f"{k} x{v}" for k, v in sorted(d.items())))

    linhas += ["", "Lista de itens ganhos (giro -> item):"]
    for it in itens:
        extra = f" ({it['detalhe']})" if it["detalhe"] else ""
        linhas.append(f"  Giro {fmt(it['giro']):>7}: {it['premio']}{extra}")
    if not itens:
        linhas.append("  (nenhum item desta vez)")
    return "\n".join(linhas)


def main():
    ap = argparse.ArgumentParser(description="Bot da roleta: giros automáticos sem animação")
    ap.add_argument("--giros", type=int, default=GIROS_PADRAO, help="quantidade de giros (padrão 14000)")
    ap.add_argument("--sem-salvar", action="store_true", help="não grava nada, só mostra o resultado")
    args = ap.parse_args()
    giros = max(1, args.giros)

    print(f"Girando {fmt(giros)} vezes, sem animação...")
    t0 = time.perf_counter()
    contagem, itens = rodar(giros)
    segundos = time.perf_counter() - t0

    relatorio = montar_relatorio(giros, contagem, itens, segundos)
    raros = [l for l in relatorio.splitlines()
             if any(n in l for n in ("Token Dourado", "Skin de Ouro", "Veículo")) and "Giro" in l]
    resumo = relatorio.split("\nLista de itens ganhos")[0]
    print("\n" + resumo)
    if raros:
        print("\nItens raros:")
        print("\n".join(raros))

    if args.sem_salvar:
        print("\n(--sem-salvar: nada foi gravado)")
        return
    salvar_roleta(giros, contagem)
    salvar_itens(giros, itens, segundos)
    with open(ARQ_RELATORIO, "w", encoding="utf-8") as f:
        f.write(relatorio)
    print("\nSalvo em:")
    print(f"  {SAVE}  (a roleta já mostra esses prêmios)")
    print(f"  {ARQ_ITENS}  (lista completa, giro a giro)")
    print(f"  {ARQ_RELATORIO}  (relatório)")

if __name__ == "__main__":
    main()

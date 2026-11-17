"""
RPA Systêxtil - baixa de OB e apontamento do rolo via teclado (pyautogui).

Jornada completa (roteiro do usuário em 17/11/2026, sobre a gravação de 10:01),
a partir de qualquer tela do Systêxtil, com o cursor no campo de BUSCA (lupa):

  Busca de tela          pcpb_f180 + Enter      -> "Baixa das Ordens de Beneficiamento Via Balança"
  F8                     leva o cursor ao Número ordem
  Número ordem           ordem + Enter, Enter, Enter -> "Tecidos Acabados da OB" (lista)
  Lista de OB            seta para baixo até a linha (teste: linha 6 = seq. tingimento 006)
  F2, F2                 -> "Entrada de rolos via balança" (fecha o alerta, se aparecer)
  F8                     prepara a linha do rolo
  Embalagens adicionais  Enter, Enter (são DOIS campos 000)
  Metros                 quantidade + Enter
  Início - Data / Hora   data + Enter / hora - 30 min + Enter
  Fim - Data / Hora      data + Enter / hora + Enter  -> GRAVA o rolo
  Logo Systêxtil         clique -> volta ao menu (Dashboard)

Modo --so-rolo: começa direto em "Embalagens adicionais" (tela de rolos já aberta).

ATENÇÃO: o Enter da Hora de fim GRAVA o rolo.

Uso:
    python apontamento_rolo.py --metros 2400 --ordem 123456 --linha 6
    python apontamento_rolo.py --metros 2400 --so-rolo
    ... --simular   (só mostra a sequência)   ... --espera 5   (contagem)

Para abortar no meio: leve o mouse para o canto superior esquerdo da tela.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timedelta

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

TELA_BUSCA = "PCPB_F180"    # código digitado na busca do Systêxtil
LUPA = "lupa_busca.png"     # imagem da lupa do campo de busca (canto superior direito)
DESLOCAMENTO_BUSCA = 100    # pixels à direita da lupa onde o robô clica (dentro do campo)
LOGO = "logo_systextil.png" # imagem do logo (canto superior esquerdo), clicada no fim para voltar ao menu
SEMELHANCA_LOGO = 0.8       # 0 a 1: quão parecido o logo na tela precisa estar com a imagem
MINUTOS_ANTES = 30          # Início = hora do computador - 30 min
SEGUNDOS_PARA_COMECAR = 10  # tempo para clicar no campo inicial
PAUSA_ENTRE_TECLAS = 0.05   # segundos entre cada caractere digitado
PAUSA_APOS_ENTER = 1.0      # espera a tela andar para o próximo campo
PAUSA_SETA = 0.3            # entre cada seta para baixo na lista de OB
ESPERA_TELA = 4             # "Aguarde..." quando o Systêxtil abre uma tela nova
ESPERA_GRAVACAO = 4         # "Aguarde..." depois do último Enter (gravação)

# Alerta "Sequência anterior não pesada": o navegador escurece a tela inteira.
# "auto" = o robô compara o brilho da janela e só aperta Enter se escureceu;
# "sempre" / "nunca" = força o comportamento.
ALERTA = "auto"
ESCURECIMENTO_ALERTA = 0.80  # brilho caiu para menos de 80% do anterior = alerta aberto

# Trava de segurança: o robô só digita se a janela ativa for a do Systêxtil.
JANELA_SYSTEXTIL = ["systêxtil", "systextil"]
JANELAS_PROIBIDAS = ["claude", "powershell", "terminal", "prompt de comando", "cmd.exe", "teams"]

FORMATO_DATA = "%d/%m/%Y"
FORMATO_HORA = "%H:%M"

# =============================================================================


class JanelaErrada(RuntimeError):
    """A janela ativa não é a do Systêxtil: o robô para sem digitar."""


# Cada passo: (tipo, descrição, valor)
#   "texto"  digita o valor e aperta Enter   "enter"  só Enter
#   "seta"   seta para baixo N vezes          "esperar" pausa de N segundos
#   "alerta" fecha o alerta se ele aparecer   "selecionar" Ctrl+A antes do texto
def passos_rolo(metros: str, agora: datetime) -> list[tuple[str, str, object]]:
    inicio = agora - timedelta(minutes=MINUTOS_ANTES)  # perto da meia-noite a data acompanha
    return [
        ("enter", "Embalagens adicionais", None),   # um Enter só (teste real 17/11 10:23)
        ("texto", "Metros", metros),
        ("texto", "Início - Data", inicio.strftime(FORMATO_DATA)),
        ("texto", "Início - Hora", inicio.strftime(FORMATO_HORA)),
        ("texto", "Fim - Data", agora.strftime(FORMATO_DATA)),
        ("texto", "Fim - Hora (GRAVA)", agora.strftime(FORMATO_HORA)),
        ("esperar", "Gravação do rolo", ESPERA_GRAVACAO),
    ]


def passos_completos(ordem: str, linha: int, metros: str, agora: datetime) -> list[tuple[str, str, object]]:
    return [
        ("janela", "Traz o Systêxtil para frente", None),
        ("busca", "Clica no campo de busca (lupa)", None),
        ("selecionar", "Busca de tela", TELA_BUSCA),
        ("esperar", "Abre Baixa das Ordens", ESPERA_TELA),
        ("tecla", "Vai para Número ordem", "f8"),
        ("esperar", "", 1),
        ("texto", "Número ordem", ordem),
        ("enter", "Data baixa (mantém)", None),
        ("enter", "Emb (mantém 000)", None),
        ("esperar", "Abre lista Tecidos Acabados da OB", ESPERA_TELA),
        ("seta", f"Lista de OB: linha {linha}", linha - 1),
        ("alerta_base", "Mede o brilho antes do F2", None),
        ("tecla", "Avança (1º F2)", "f2"),
        ("esperar", "", 2),
        ("alerta", "Alerta 'Sequência anterior não pesada'", None),
        ("tecla", "Avança (2º F2)", "f2"),
        ("esperar", "Abre Entrada de rolos via balança", ESPERA_TELA),
        ("alerta", "Alerta 'Sequência anterior não pesada'", None),
        ("tecla", "Prepara a linha do rolo", "f8"),
        ("esperar", "", 1),
        *passos_rolo(metros, agora),
        ("logo", "Clica no logo Systêxtil (volta ao menu)", None),
        ("esperar", "Abre o menu", 2),
    ]


def normalizar_metros(texto: str) -> str:
    """Aceita 2400, 2400,5 ou 2400.5 e devolve no padrão brasileiro (vírgula)."""
    valor = texto.strip().replace(".", ",") if texto.count(",") == 0 else texto.strip()
    numero = float(valor.replace(".", "").replace(",", "."))
    if numero <= 0:
        raise ValueError("a quantidade precisa ser maior que zero")
    return valor


def conferir_janela(teclado) -> None:
    titulo = (teclado.getActiveWindowTitle() or "").strip()
    minusculo = titulo.casefold()
    if any(p in minusculo for p in JANELAS_PROIBIDAS) or not any(s in minusculo for s in JANELA_SYSTEXTIL):
        raise JanelaErrada(
            f"a janela ativa é '{titulo}', não o Systêxtil. Nada foi digitado nesta etapa. "
            "Se essa for mesmo a janela do Systêxtil, inclua um pedaço do título em JANELA_SYSTEXTIL.")


def brilho_janela(teclado) -> float:
    """Brilho médio (0-255) da janela ativa, para perceber o escurecimento do alerta."""
    janela = teclado.getActiveWindow()
    regiao = (janela.left, janela.top, janela.width, janela.height) if janela else None
    imagem = teclado.screenshot(region=regiao).convert("L").resize((200, 120))
    dados = imagem.getdata()
    return sum(dados) / len(dados)


def trazer_systextil(teclado) -> None:
    """Traz para frente a janela cujo título tem 'Systêxtil' (o robô não depende de clique do operador)."""
    import pygetwindow
    candidatas = [
        j for j in pygetwindow.getAllWindows()
        if j.title and any(s in j.title.casefold() for s in JANELA_SYSTEXTIL)
        and not any(p in j.title.casefold() for p in JANELAS_PROIBIDAS)
    ]
    if not candidatas:
        raise JanelaErrada("nenhuma janela com 'Systêxtil' no título está aberta. Abra o Systêxtil e rode de novo.")
    janela = candidatas[0]
    try:
        if janela.isMinimized:
            janela.restore()
        janela.activate()
    except Exception:  # noqa: BLE001 - o Windows às vezes recusa trazer para frente; tenta minimizar e restaurar
        janela.minimize()
        janela.restore()
    time.sleep(1)
    print(f"      Janela ativada: '{janela.title}'")


def clicar_busca(teclado) -> None:
    """Acha a lupa do campo de busca e clica dentro do campo, à direita dela."""
    from pathlib import Path
    imagem = str(Path(__file__).resolve().parent / LUPA)
    try:
        achado = teclado.locateCenterOnScreen(imagem, confidence=0.85)
    except Exception:  # noqa: BLE001
        achado = None
    if not achado:
        raise JanelaErrada("não achei a lupa do campo de busca na tela. Deixe o Systêxtil visível e maximizado.")
    teclado.click(achado.x + DESLOCAMENTO_BUSCA, achado.y)
    time.sleep(0.5)
    print(f"      Campo de busca clicado em ({achado.x + DESLOCAMENTO_BUSCA}, {achado.y}).")


def clicar_logo(teclado) -> None:
    """Acha o logo do Systêxtil na tela e clica no centro dele. Se não achar, avisa e não clica."""
    from pathlib import Path
    imagem = str(Path(__file__).resolve().parent / LOGO)
    try:
        achado = teclado.locateCenterOnScreen(imagem, confidence=SEMELHANCA_LOGO)
    except Exception:  # noqa: BLE001 - pyscreeze lança exceção quando não acha
        achado = None
    if not achado:
        print("      Logo do Systêxtil não encontrado na tela: o rolo já foi gravado; volte ao menu na mão.")
        return
    teclado.click(achado.x, achado.y)
    print(f"      Logo encontrado em ({achado.x}, {achado.y}) e clicado.")


def caps_lock_ligado() -> bool:
    import ctypes
    return bool(ctypes.windll.user32.GetKeyState(0x14) & 1)


def executar(passos, simular: bool) -> None:
    if simular:
        _executar(passos, None)
        return
    import pyautogui as teclado   # importado só aqui: a simulação roda sem a biblioteca
    teclado.FAILSAFE = True       # mouse no canto superior esquerdo aborta
    # Com Caps Lock ligado, "PCPB_F180" sairia "pcpb_f180": desliga durante a digitação e religa no fim.
    caps = caps_lock_ligado()
    if caps:
        teclado.press("capslock")
    try:
        _executar(passos, teclado)
    finally:
        # Religa sem consultar de novo: no Windows, a leitura feita pelo mesmo processo
        # depois de apertar a tecla pode vir desatualizada.
        if caps:
            teclado.press("capslock")


def _executar(passos, teclado) -> None:
    simular = teclado is None

    base = None
    for n, (tipo, campo, valor) in enumerate(passos, 1):
        descricao = {
            "texto": f"digita '{valor}' + Enter",
            "selecionar": f"Ctrl+A, digita '{valor}' + Enter",
            "enter": "Enter",
            "seta": f"seta para baixo x{valor} ",
            "esperar": f"espera {valor} s",
            "alerta_base": "",
            "alerta": f"Enter se o alerta aparecer ({ALERTA})",
            "tecla": f"aperta {str(valor).upper()}",
            "logo": "procura a imagem do logo e clica",
            "janela": "ativa a janela pelo título",
            "busca": "procura a lupa e clica no campo",
        }[tipo]
        if tipo != "alerta_base" and campo:
            print(f"  {n:2d}. {campo:<40} {descricao}", flush=True)
        if simular:
            continue

        if tipo == "esperar":
            time.sleep(valor)
            continue
        if tipo == "janela":
            trazer_systextil(teclado)
        conferir_janela(teclado)   # antes de cada ação: se trocou de janela, para
        if tipo == "alerta_base":
            base = brilho_janela(teclado) if ALERTA == "auto" else None
        elif tipo == "alerta":
            if ALERTA == "sempre":
                aberto = True
            elif ALERTA == "nunca":
                aberto = False
            else:
                agora = brilho_janela(teclado)
                aberto = bool(base) and agora < base * ESCURECIMENTO_ALERTA
                print(f"      brilho {base:.0f} -> {agora:.0f}: alerta {'aberto' if aberto else 'não apareceu'}")
            if aberto:
                teclado.press("enter")
                time.sleep(PAUSA_APOS_ENTER)
        elif tipo == "tecla":
            teclado.press(valor)
            time.sleep(PAUSA_APOS_ENTER)
        elif tipo == "logo":
            clicar_logo(teclado)
        elif tipo == "janela":
            pass   # já ativada acima, antes da trava
        elif tipo == "busca":
            clicar_busca(teclado)
        elif tipo == "seta":
            for _ in range(valor):
                teclado.press("down")
                time.sleep(PAUSA_SETA)
        else:
            if tipo == "selecionar":
                teclado.hotkey("ctrl", "a")
            if valor is not None:
                teclado.write(str(valor), interval=PAUSA_ENTRE_TECLAS)
            teclado.press("enter")
            time.sleep(PAUSA_APOS_ENTER)


def main() -> int:
    parser = argparse.ArgumentParser(description="Baixa de OB e apontamento do rolo no Systêxtil.")
    parser.add_argument("--metros", help="quantidade capturada (ex.: 2400 ou 2400,5)")
    parser.add_argument("--ordem", help="número da ordem de beneficiamento (ex.: 123456)")
    parser.add_argument("--linha", type=int, help="linha da lista 'Tecidos Acabados da OB' (1 = primeira)")
    parser.add_argument("--so-rolo", action="store_true",
                        help="começa direto em 'Embalagens adicionais' (tela de rolos já aberta)")
    parser.add_argument("--simular", action="store_true", help="só mostra a sequência, sem digitar")
    parser.add_argument("--espera", type=int, default=SEGUNDOS_PARA_COMECAR,
                        help=f"segundos de contagem antes de começar (padrão {SEGUNDOS_PARA_COMECAR})")
    args = parser.parse_args()

    bruto = args.metros or input("Quantidade capturada (metros): ")
    try:
        metros = normalizar_metros(bruto)
    except ValueError as erro:
        print(f"Quantidade inválida ({bruto!r}): {erro}")
        return 2

    if not args.so_rolo:
        ordem = (args.ordem or input("Número da ordem: ")).strip()
        linha = args.linha or int(input("Linha da OB na lista (1 = primeira): "))
        if not ordem.isdigit() or linha < 1:
            print("Ordem precisa ser numérica e a linha, 1 ou mais.")
            return 2
        inicio_campo = None   # o robô traz o Systêxtil para frente e clica na busca sozinho
    else:
        inicio_campo = "o campo 'Embalagens adicionais' do Systêxtil"

    if not args.simular:
        if inicio_campo:
            print(f"Clique n{inicio_campo}. Começando em {args.espera} s...")
        else:
            print(f"Deixe o Systêxtil aberto (qualquer tela). O robô traz a janela e clica na busca. "
                  f"Começando em {args.espera} s...")
        for falta in range(args.espera, 0, -1):
            print(f"  {falta}...", flush=True)
            time.sleep(1)

    agora = datetime.now()   # hora capturada no momento da digitação
    passos = passos_rolo(metros, agora) if args.so_rolo else passos_completos(ordem, linha, metros, agora)
    print(("SIMULAÇÃO - " if args.simular else "") + f"hora do computador: {agora:%d/%m/%Y %H:%M:%S}")
    try:
        executar(passos, args.simular)
    except Exception as erro:  # noqa: BLE001 - inclui o FailSafe do pyautogui
        print(f"Interrompido: {type(erro).__name__}: {erro}")
        return 1
    print("Pronto. O último Enter grava o rolo: confira na tela se apareceu o número do rolo "
          "e se o cursor voltou para 'Embalagens adicionais'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

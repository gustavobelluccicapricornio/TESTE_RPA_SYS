# RPA Systêxtil – Apontamento de rolo

Automação em **Python + pyautogui** que faz a baixa da OB e grava o apontamento de um rolo no **Systêxtil**, a partir do campo de busca (modo completo) ou da tela de rolos já aberta (`--so-rolo`). O robô usa só o teclado: digita cada valor e aperta Enter, igual ao operador.

> **Situação (17/11/2026):** **os dois modos foram validados na tela real.** O **modo completo** (busca PCPB_F180 → ordem 123456 → linha 6 → F2, F2 → F8 → rolo → logo) rodou às 10:26 e gravou o rolo de 2400 m corretamente, com confirmação do usuário. O modo **só o rolo** foi validado às 08:11. A origem da quantidade (balança, medidor, sistema) ainda não foi definida: por enquanto ela é digitada na mão.

---

## 1. Mapa das pastas

```
Downloads\
├── systextil_rpa\                  ← este RPA
│   ├── apontamento_rolo.py         # robô (configuração no topo do arquivo)
│   ├── rodar_apontamento.bat       # atalho: chama o Python do ambiente conda pelo caminho completo
│   ├── logo_systextil.png          # imagem do logo, clicada no fim para voltar ao menu
│   ├── README.md                   # este arquivo
│   └── __pycache__\                # gerado pelo Python, pode apagar
│
└── deps_rpa\                       ← RPA irmão (consulta de crédito no DEPS, Playwright)
    ├── deps_consulta_cnpj.py
    ├── cnpjs.txt
    └── README.md

%LOCALAPPDATA%\miniconda3\
└── envs\systextil-rpa\             ← ambiente Python deste RPA
    └── python.exe                  # Python 3.12 + pyautogui (+ opencv, usado só para analisar vídeo)
```

| Item | Para que serve | Pode apagar? |
|---|---|---|
| `apontamento_rolo.py` | Lógica do robô e configuração | Não |
| `rodar_apontamento.bat` | Forma de rodar sem depender do PATH | Não |
| `README.md` | Documentação | Não |
| `__pycache__\` | Cache do Python | Sim, ele recria |
| Ambiente `systextil-rpa` | Python e bibliotecas do robô | Só se for recriar (seção 3) |

---

## 2. Fluxo do processo

Mapeado na gravação de tela de 17/11/2026 10:01 (jornada completa). Há dois modos:

- **Completo (padrão):** começa em qualquer tela do Systêxtil, com o cursor no **campo de busca** (lupa, canto superior direito).
- **Só o rolo (`--so-rolo`):** começa com a tela *Entrada de rolos via balança* já aberta e o cursor em **Embalagens adicionais** (passos 9 a 13).

| Passo | Tela / campo | O robô faz |
|---|---|---|
| 1 | Busca de tela | Ctrl+A, digita `pcpb_f180`, Enter → abre *Baixa das Ordens de Beneficiamento Via Balança* |
| 2 | — | **F8** (leva o cursor ao Número ordem) |
| 3 | Número ordem | digita a ordem (ex.: `123456`), Enter, Enter, Enter → abre a lista *Tecidos Acabados da OB* |
| 4 | Lista de OB | seta para baixo até a linha pedida (`--linha`; no teste, linha 6 = seq. tingimento 006) |
| 5 | — | **F2**, **F2** → abre *Entrada de rolos via balança*. Se o alerta "Sequência anterior não pesada" aparecer, Enter (OK) |
| 6 | — | **F8** (prepara a linha do rolo) |
| 7 | (depois de gravar) | clica no **logo Systêxtil** → volta ao menu. O robô acha o logo pela imagem `logo_systextil.png` |
| 8–9 | Embalagens adicionais | **um** Enter (mantém `000`) |
| 10 | Metros | quantidade capturada, Enter |
| 11 | Início – Data / Hora | data do computador, Enter / hora **− 30 min**, Enter |
| 12 | Fim – Data | data do computador, Enter |
| 13 | Fim – Hora | hora do computador, Enter → **grava o rolo** |

O que as gravações de tela mostraram e o robô respeita:

- **Embalagens adicionais: um Enter só.** O vídeo de 17/11 sugeria dois campos `000`, mas no teste real de 10:23 dois Enter jogaram a metragem no campo de data. Com um Enter, o cursor cai em **Metros** (corrigido às 10:26).
- **O robô traz o Systêxtil para frente e clica na busca sozinho:** acha a janela pelo título e o campo pela imagem `lupa_busca.png`.
- **Roteiro de teclas** (F8 → ordem → Enter ×3 → linha → F2, F2 → F8) passado pelo usuário em 17/11/2026.
- **A lista de OB não é lida pelo robô.** Ele desce `linha − 1` vezes a partir da primeira. No teste, a linha 6 é a seq. tingimento 006 (as linhas 5 e 6 foram liberadas para apontar).
- **Logo:** o recorte não inclui a linha "Release: ...", que muda a cada versão. Se o Systêxtil mudar o visual do logo, recorte de novo.
- **O alerta** "Sequência anterior não pesada" escurece a tela inteira. No modo `ALERTA = "auto"`, o robô compara o brilho da janela antes e depois e só aperta Enter se escureceu.
- **Caps Lock:** com ele ligado, `PCPB_F180` sairia em minúsculas. O robô desliga durante a digitação e religa no fim.
- O Enter em **Metros** vai direto para **Início – Data**. Os campos Peso, Lote e Nuance não recebem o cursor.
- Cada campo já chega com o conteúdo **selecionado**, então o que é digitado substitui o valor (`LIMPAR_CAMPO = False`).
- O **Enter da Hora de fim grava**: aparece "Aguarde...", o Systêxtil cria o número do rolo, soma em *Qtde prod.* e *Rolos prod.*, abre a linha seguinte e devolve o cursor para *Embalagens adicionais*. Ou seja, a tela fica pronta para o próximo rolo.
- Perto da meia-noite, "30 minutos antes" pode cair no dia anterior. Nesse caso a **data de início** acompanha.

---

## 3. Instalação (uma vez só)

Nesta máquina **não há Python avulso**, e o `conda` **não está no PATH** do PowerShell (`conda`, `python` e `pip` dão "não reconhecido"). Por isso, tudo usa o caminho completo do ambiente.

O ambiente `systextil-rpa` já foi criado em 16/11/2026. Para recriar:

```bash
& "$env:LOCALAPPDATA\miniconda3\Scripts\conda.exe" create -y -n systextil-rpa python=3.12
```

```bash
& "$env:LOCALAPPDATA\miniconda3\envs\systextil-rpa\python.exe" -m pip install pyautogui
```

---

## 4. Execução

**Modo completo** (metros, ordem e linha da OB):

```bash
& "$env:USERPROFILE\Downloads\systextil_rpa\rodar_apontamento.bat" 2400 --ordem 123456 --linha 6
```

Durante a contagem, clique no **campo de busca** (lupa) do Systêxtil.

**Só o rolo** (tela de rolos já aberta):

```bash
& "$env:USERPROFILE\Downloads\systextil_rpa\rodar_apontamento.bat" 2400 --so-rolo
```

Durante a contagem, clique em **Embalagens adicionais**.

Por duplo clique no `.bat`, o robô pergunta a quantidade, a ordem e a linha. Não mexa no teclado nem no mouse até aparecer **"Pronto"**.

Para mudar a contagem (por exemplo, 5 segundos em vez de 10):

```bash
& "$env:USERPROFILE\Downloads\systextil_rpa\rodar_apontamento.bat" 2400 --espera 5
```

Para ver a sequência sem digitar nada:

```bash
& "$env:USERPROFILE\Downloads\systextil_rpa\rodar_apontamento.bat" 2400 --simular
```

**Para abortar:** leve o mouse ao **canto superior esquerdo** da tela (FailSafe do pyautogui).

Código de saída: `0` terminou, `1` interrompido (janela errada ou FailSafe), `2` quantidade inválida.

---

## 5. Configuração

Tudo fica no bloco `CONFIGURAÇÃO`, no topo de `apontamento_rolo.py`.

| Constante | Valor | Para que serve |
|---|---|---|
| `TELA_BUSCA` | `pcpb_f180` | Código digitado na busca para abrir a baixa de OB |
| `ESPERA_TELA` | `4` | Espera do "Aguarde..." quando abre uma tela nova |
| `PAUSA_SETA` | `0.3` | Intervalo entre setas na lista de OB |
| `ALERTA` | `auto` | Alerta "Sequência anterior não pesada": `auto` (mede o brilho), `sempre` ou `nunca` |
| `ESCURECIMENTO_ALERTA` | `0.80` | Considera o alerta aberto se o brilho cair abaixo de 80% |
| `MINUTOS_ANTES` | `30` | Início = hora do computador − N minutos |
| `SEGUNDOS_PARA_COMECAR` | `10` | Tempo para clicar no campo antes de começar |
| `PAUSA_ENTRE_TECLAS` | `0.05` | Intervalo entre caracteres digitados |
| `PAUSA_APOS_ENTER` | `1.0` | Espera a tela andar para o próximo campo |
| `ESPERA_GRAVACAO` | `4` | Tempo do "Aguarde..." depois do último Enter |
| `LIMPAR_CAMPO` | `False` | `True` = Home + Shift+End + Delete antes de digitar |
| `JANELA_SYSTEXTIL` | `systêxtil`, `systextil` | O título da janela ativa precisa ter um destes textos |
| `JANELAS_PROIBIDAS` | `claude`, `powershell`, `terminal`... | O robô para se a janela ativa for uma destas |
| `FORMATO_DATA` / `FORMATO_HORA` | `%d/%m/%Y` / `%H:%M` | Troque por `%d%m%Y` / `%H%M` se a máscara recusar as barras ou os dois-pontos |
| Sequência de passos | funções `passos_completos` e `passos_rolo` | Ordem dos campos. Ajuste ali se a tela mudar |

---

## 6. Segurança

- **Trava de janela.** Antes de **cada** campo, o robô lê o título da janela ativa. Se não for o Systêxtil, ele para sem digitar. A trava foi criada depois que, num teste, o robô digitou na caixa de mensagem do Claude (16/11/2026).
- **O robô grava.** Cada execução cria um rolo real e soma na produção da ordem. Teste só onde o rolo puder ser excluído depois.
- **O robô não confere a tela.** Ele não lê o número do rolo gerado nem mensagens de erro do Systêxtil. Se o cursor não estiver em *Embalagens adicionais*, os valores caem no campo errado. A trava só garante a janela, não o campo.
- Use o usuário do Systêxtil do próprio operador, ou um usuário do robô, para que os apontamentos fiquem rastreáveis.

---

## 7. Pontos a validar

| Ponto | Situação |
|---|---|
| Execução completa na tela real | **Validado** em 17/11/2026 08:11 (rolo gravado corretamente), ainda com um Enter só em Embalagens |
| Modo completo (pcpb_f180 → F8 → OB → F2, F2 → F8 → rolo → logo) | **Pendente:** testado só na janela falsa (17/11/2026 10:18) |
| Modo completo na tela real (17/11 10:26) | Rodou até o fim: busca, F8, ordem, linha 6, alerta detectado e fechado, F2, F2, F8, rolo com um Enter em Embalagens, logo clicado. **Validado:** rolo gravado corretamente (confirmado pelo usuário) |
| Detecção do alerta pelo brilho | Não testada com o alerta real. Se falhar, usar `ALERTA = "sempre"` ou `"nunca"` |
| Escolha da linha da OB | O robô não lê a lista. Confirmar a regra: qual linha o operador escolhe |
| Rolos gravados durante os testes | Cada execução grava um rolo real: excluir no Systêxtil os que forem só teste |
| Origem da "quantidade capturada" | **Indefinida:** hoje é digitada na mão |
| Regra "início = fim − 30 min" | Confirmar com a produção o dono da regra |
| Embalagens adicionais | Hoje mantém o `000` da tela. Confirmar se algum dia precisa ser preenchido |
| Título da janela do Systêxtil | A trava passou nos testes. Se mudar de navegador ou de versão, conferir |
| Leitura do número do rolo gerado | Não implementado (seção 8) |

---

## 8. Horizonte: disparo por JSON (não implementado)

> Esta seção é **só desenho**. Nada disso existe no código ainda. Fica registrado para orientar a próxima etapa, sem compromisso de prazo.

**Ideia:** em vez de alguém rodar o atalho e digitar a quantidade, um sistema de origem (balança, medidor de metros, Power Automate, outro sistema) **deposita um arquivo JSON** e o robô faz o apontamento sozinho.

### Formato proposto

```json
{
  "id": "2026-11-16T20:25:32-maq07-0001",
  "origem": "medidor-maq07",
  "metros": 2400.0,
  "ordem": "123456",
  "linha": 6,
  "embalagens_adicionais": 0,
  "fim": "2026-11-16T20:25:32",
  "minutos_antes": 30,
  "ordem_destino": "123457"
}
```

| Campo | Obrigatório | Uso |
|---|---|---|
| `id` | Sim | Identificador único. O robô nunca aponta o mesmo `id` duas vezes |
| `origem` | Sim | Quem gerou o pedido, para rastreio |
| `metros` | Sim | Quantidade de Metros |
| `ordem` / `linha` | Sim no modo completo | Número da ordem e linha da lista de OB |
| `fim` | Não | Hora de fim. Se vier vazio, usa a hora do computador |
| `minutos_antes` | Não | Se vier vazio, usa `MINUTOS_ANTES` |
| `embalagens_adicionais` | Não | Se vier vazio, mantém o valor da tela |
| `ordem_destino` | Não | Para conferir se a tela aberta é da ordem certa (exige ler a tela) |

### Fluxo proposto

```
systextil_rpa\
├── fila\entrada\      ← o sistema de origem grava aqui o *.json
├── fila\processado\   ← o robô move depois de gravar (com o resultado anexado)
├── fila\erro\         ← o robô move se falhar (com o motivo)
└── apontamentos.log   ← histórico: id, horário, valores, resultado
```

1. Um **vigia** (laço com intervalo, ou o Agendador de Tarefas) olha `fila\entrada\`.
2. Para cada JSON: valida os campos e confere se o `id` já foi processado.
3. Chama a mesma função de hoje (`montar_passos` + `executar`) com os valores do JSON. Fica um código só, com dois jeitos de disparar.
4. Move o arquivo para `processado\` ou `erro\` e grava no log.

### O que precisa ser resolvido antes

- **Foco sem ninguém clicar.** Hoje o operador clica no campo. Sem pessoa, o robô precisa trazer a janela do Systêxtil para frente sozinho e garantir o cursor em *Embalagens adicionais*. Como depois de cada gravação o cursor volta para esse campo, isso ajuda.
- **Sessão desbloqueada.** O pyautogui não digita com a tela bloqueada nem com a sessão do Windows desconectada. Seria preciso uma máquina dedicada, logada e com a tela aberta.
- **Confirmação da gravação.** Para marcar um JSON como processado, o robô precisa ver que o rolo foi criado. Opções: ler a tela por OCR, conferir no banco ou na API do Systêxtil, ou usar uma integração direta.
- **Alternativa mais robusta:** se o Systêxtil tiver API ou importação para apontamento de produção, o JSON pode ir direto para ela, sem automação de tela. Vale perguntar à Systêxtil antes de investir no vigia.
- **Concorrência:** um JSON por vez, nunca dois robôs na mesma tela.

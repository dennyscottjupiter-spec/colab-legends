---
title: Legendas PT-BR — do seu MP4 até o .srt pronto
status: current
updated: 2026-09-07
---

# Legendas PT-BR em 3 passos

Transforma um vídeo em arquivo de legendas `.srt` em português.

**O vídeo nunca sai do seu PC.** Só o áudio (`.mp3`, ~30 MB por hora) sobe para o Google Colab,
que empresta uma GPU de graça para rodar o modelo de transcrição.

```
seu_video.mp4  --(seu PC)-->  seu_video.mp3  --(Colab, GPU grátis)-->  seu_video_bruto.srt
                                                                       seu_video.srt  (revisado)
```

No Colab acontecem duas coisas, uma depois da outra: o áudio vira texto com horários, e esse texto
passa por uma **revisão de português** feita por um segundo modelo na mesma GPU. Você recebe os
dois arquivos — o cru e o revisado.

### Três palavras que aparecem o tempo todo

Se algum destes nomes for novo para você, leia aqui antes de começar — o resto do texto usa os três:

- **Google Colab** — um site do Google onde você roda código sem instalar nada. Ele te empresta um
  computador virtual na nuvem, de graça, por algumas horas.
- **GPU T4** — a placa de vídeo desse computador emprestado. É ela que faz a transcrição levar
  minutos em vez de horas. O notebook já pede a T4 sozinho.
- **`.srt`** — o arquivo de legenda. É texto puro: número da legenda, o horário em que ela entra e
  sai da tela, e a frase. Qualquer player (VLC, YouTube, TV) entende.

---

## Antes da primeira vez (uma vez só)

Abra o PowerShell nesta pasta e rode:

```powershell
python3 -m pip install imageio-ffmpeg
```

Isso instala o conversor de áudio. Não precisa de mais nada — nem conta paga, nem programa instalado.

> **Como abrir o PowerShell já nesta pasta:** abra a pasta `colab-legends` no Explorador de
> Arquivos, clique com o botão direito num espaço vazio e escolha **Abrir no Terminal**.

---

## Passo 1 — Jogue o vídeo aqui e converta

1. **Copie o seu vídeo para esta pasta** (`colab-legends`).
2. **Dê duplo clique em `CONVERTER.cmd`.**

Pronto. Aparece um `seu_video.mp3` do lado do vídeo.

> Também dá para **arrastar o vídeo em cima do `CONVERTER.cmd`** — funciona igual, sem precisar copiar antes.
> O duplo clique converte **todos** os vídeos da pasta de uma vez, e pula os que já têm `.mp3`.

Formatos aceitos: `.mp4`, `.mkv`, `.mov`, `.avi`, `.webm`, `.m4v`.

O `.mp3` sai bem menor que o vídeo de propósito — é só a faixa de voz, no formato exato que o
modelo usa. Um vídeo de 1 hora vira um `.mp3` de ~30 MB.

---

## Passo 2 — Transcreva no Colab

1. Abra <https://colab.research.google.com> → botão **Fazer upload de notebook** → escolha
   `transcrever_ptbr_colab.ipynb`.
2. **Suba o `.mp3`:** clique no ícone de **pasta** na barra esquerda (painel *Arquivos*) e arraste o `.mp3` para lá.
   Espere a bolinha de progresso terminar.
3. Menu `Ambiente de execução` → **`Executar tudo`**.

O notebook **já pede a GPU T4 sozinho** — não precisa mexer no menu de ambiente de execução.
Se mesmo assim a célula 3 parar avisando **SEM GPU**, ligue na mão:
`Ambiente de execução` → `Alterar o tipo de ambiente de execução` → **T4 GPU** → `Salvar`.

Agora é só esperar. A célula 3 mostra o texto aparecendo com a porcentagem do progresso.

### ⚠️ Passo 2.1 — O `.mp3` tem que cair **dentro da pasta `content`**

Este é **o erro número 1** de quem usa o notebook pela primeira vez. Vale a pena ler os
três parágrafos abaixo antes de arrastar o arquivo.

O painel *Arquivos* (o ícone de pasta na barra esquerda) mostra o disco do computador virtual que o
Google te emprestou. Quando o painel abre, ele já está **dentro de uma pasta chamada `content`** —
essa é a pasta de trabalho, a única que o notebook olha.

O notebook procura o áudio com uma busca **não recursiva**: ele lista os `.mp3` que estão
**soltos dentro de `content`** e ignora tudo o que estiver em subpastas. Se o seu `.mp3` cair em
qualquer outro lugar, a célula 2 não acha nada, cai no widget antigo de upload
(o `Escolher arquivos` que trava com arquivo grande) e parece que o notebook quebrou — mas não quebrou.

**Onde soltar o arquivo:** exatamente na lista que já está aberta quando o painel *Arquivos* carrega
— a pasta `content`. Arraste o `.mp3` para o meio dessa lista e espere a bolinha de progresso fechar
o círculo. Quando terminar, o nome do seu arquivo aparece ali, na mesma altura de `sample_data`.

#### Onde **NÃO** colocar

| Lugar errado | Por que não funciona |
|---|---|
| `/` (a raiz, com `bin`, `boot`, `dev`, `etc`, `usr`, `lib`…) | São as pastas de sistema do Linux da máquina virtual. O notebook não olha lá — e você não deve mexer nelas. Se você clicou na setinha **para cima** e a lista mudou, você saiu de `content`. |
| `sample_data/` | É uma subpasta de exemplo que o Colab cria sozinho. Está *dentro* de `content`, mas a busca não entra em subpastas. |
| Qualquer subpasta que você criar | Mesmo problema: a busca não é recursiva, só enxerga o primeiro nível de `content`. |
| `drive/MyDrive/...` (Google Drive montado) | É outro caminho, fora de `content`. O notebook não procura no Drive. |

> **Ficou na dúvida?** Passe o mouse em cima do arquivo no painel *Arquivos*, clique nos três
> pontinhos → **Copiar caminho**. Tem que aparecer `/content/seu_video.mp3` — com **uma** barra só
> antes de `content` e **nada** entre `content` e o nome do arquivo.

#### O `/content` é apagado quando o ambiente reinicia

A pasta `content` vive na máquina emprestada, não no seu PC nem na sua conta. **Se o ambiente do
Colab desconectar ou reiniciar, tudo o que estava em `content` some** — inclusive o `.mp3` que você
acabou de subir. É normal e não tem conserto: é só subir o arquivo de novo e rodar
`Ambiente de execução` → `Executar tudo` outra vez.

Por isso, **nunca aceite o aviso "você está conectado a uma GPU mas não está usando"**. Aceitar essa
troca reinicia o ambiente e apaga o seu `.mp3`. Feche o aviso e ignore.

---

## Passo 3 — Pegue o `.srt`

No fim, **saem dois arquivos** e o navegador baixa os dois sozinho:

| Arquivo | O que é |
|---|---|
| `seu_video.srt` | **O bom.** Já passou pela revisão de português. É este que você usa. |
| `seu_video_bruto.srt` | A transcrição crua, sem revisão. Serve para comparar — e é a rede de segurança se o Colab cair no meio da revisão. |

O bruto sai primeiro, assim que as legendas ficam prontas; o revisado sai alguns minutos depois.
Se algum download não começar, clique com o botão direito no arquivo dentro do painel *Arquivos*
e escolha **Fazer download**.

Arraste o `.srt` para dentro do VLC (ou deixe com o mesmo nome do vídeo, na mesma pasta,
que qualquer player carrega sozinho).

### O que a revisão conserta (e o que ela nunca faz)

Depois da transcrição, o mesmo Colab carrega um segundo modelo — o **Qwen3-8B**, um modelo de
linguagem — e passa as legendas por ele em blocos de 25. Ele lê **só o texto**: os horários nunca
saem do notebook, então não tem como a revisão dessincronizar a legenda.

- **Conserta:** ponto final que falta, vírgula, dois-pontos, maiúscula depois de ponto, acento,
  crase, concordância, palavra que o reconhecimento de fala trocou, confusão de "sessão/seção",
  nome próprio sem maiúscula, hífen de diálogo.
- **Nunca faz:** reescrever a frase, trocar palavra por sinônimo, juntar ou dividir legendas,
  traduzir, resumir, nem inventar o que faltou — ele não ouviu o áudio.

Se a resposta do modelo vier estranha em algum bloco, o notebook tenta de novo uma vez e, se ainda
assim não bater, **fica com o texto original daquele bloco**. Legenda que ficaria grande demais
para a tela também volta ao original. Ou seja: a revisão só pode melhorar ou empatar.

Uma legenda quase sempre é um pedaço de frase que continua na legenda seguinte, e o revisor tem
mania de "fechar" esse pedaço com uma vírgula que não existe ("ela se torna," / "que privilegie,").
O notebook não tenta convencer o modelo disso: ele **recusa no código** qualquer pontuação nova no
fim de uma legenda cuja próxima começa com letra minúscula — sinal de que a frase continua lá.

Para desligar a revisão, mude `POLIR = True` para `POLIR = False` no topo da célula 5.
Aí o `.srt` final sai igualzinho ao bruto.

---

## Quanto tempo demora

| Vídeo | MP3 gerado | Transcrição no Colab (T4) | Revisão do português |
|---|---|---|---|
| 45 s | 0,4 MB | ~4 s | ~10 s |
| 5 min | 2,4 MB | ~22 s | ~1 min |
| 1 hora | ~30 MB | ~4 a 6 min | ~5 a 8 min |
| 2 horas | ~57 MB | ~8 a 12 min | ~10 a 16 min |

Some ainda um tempo fixo de preparação, só na primeira vez de cada sessão do Colab:
~2 min baixando o modelo `large-v3` (~3 GB) e mais ~3 min baixando o revisor Qwen3-8B (~5 GB)
junto com a biblioteca que o roda (~1,7 GB). Nada disso fica no seu PC.

> Com pressa? `POLIR = False` no topo da célula 5 pula a revisão inteira — aí vale só a coluna
> da transcrição, e o `.srt` final sai igual ao bruto.

---

## Se der problema

| O que aconteceu | O que fazer |
|---|---|
| `CONVERTER.cmd` abre e fecha na hora | Falta o `python3` no PATH. Rode `python3 --version` no PowerShell. |
| `ffmpeg nao encontrado` | Rode `python3 -m pip install imageio-ffmpeg`. |
| `FALHOU (arquivo sem audio ou corrompido)` | O arquivo não tem faixa de áudio (ou está quebrado). Os outros vídeos da pasta continuam sendo convertidos. |
| Notebook para dizendo **SEM GPU** | A GPU grátis acabou por hoje ou não foi ligada. Ligue a T4 (passo 2) e rode `Executar tudo` de novo, ou tente mais tarde. |
| Aviso **"você está conectado a uma GPU mas não está usando"** | Feche e ignore. Aceitar a troca reinicia o ambiente e apaga o `.mp3` que você subiu. |
| A célula 2 pediu upload em vez de achar o arquivo | O `.mp3` não terminou de subir no painel *Arquivos*. Espere e rode a célula de novo. |
| **O `.mp3` foi parar na pasta errada** | O notebook só enxerga `.mp3` soltos dentro de `content` — não entra em `sample_data/`, nem em subpastas, nem na raiz `/`, nem no Drive. Arraste o arquivo para a lista que abre por padrão no painel *Arquivos* e confira com **Copiar caminho**: tem que ser `/content/seu_video.mp3`. Depois rode a célula 2 de novo. |
| **O painel *Arquivos* ficou vazio / o `.mp3` sumiu** | O ambiente do Colab reiniciou ou desconectou, e isso apaga tudo o que estava em `content`. Suba o `.mp3` de novo e rode `Ambiente de execução` → `Executar tudo`. Para não repetir, nunca aceite o aviso de "GPU não usada". |
| A célula 2 pegou o mp3 errado | Tem mais de um `.mp3` no Colab. Apague os outros no painel *Arquivos*. |
| O `.srt` não baixou sozinho | Painel *Arquivos* → botão direito no `.srt` → **Fazer download**. |
| **Saiu só o `_bruto.srt`** | A revisão não chegou ao fim (Colab caiu, GPU acabou, ou você parou). O bruto é legenda completa e sincronizada — dá para usar. Para tentar a revisão de novo, rode as células 5, 6 e 7 outra vez. |
| A célula 5 diz **"resposta invalida duas vezes"** | Normal e inofensivo: aquele bloco de 25 legendas ficou com o texto original. Se aparecer em quase todos os blocos, desligue com `POLIR = False` e use o bruto. |
| A célula 5 parou dizendo que **falta CUDA** | O ambiente não é o esperado. Confirme a T4 (passo 2) e rode `Ambiente de execução` → `Executar tudo` de novo. |
| A revisão está demorando demais | É o preço do segundo modelo. Ou espera (o `_bruto.srt` já está salvo), ou interrompe e usa o bruto, ou roda de novo com `POLIR = False`. |
| O Colab desconectou no meio | A sessão grátis cai sozinha se ficar ociosa (o tempo exato não é publicado) e dura no máximo 12 h. Reabra, suba o mp3, `Executar tudo`. |

---

## O que tem nesta pasta

| Arquivo | Para quê |
|---|---|
| `CONVERTER.cmd` | O botão. Duplo clique ou arraste o vídeo em cima. |
| `mp4_para_mp3.py` | O script que o `.cmd` chama (dá para rodar direto no PowerShell também). |
| `transcrever_ptbr_colab.ipynb` | O notebook que roda no Colab. |
| `exemplo/` | Vídeo de teste + o `.mp3` e o `.srt` que ele gerou, para comparação. |
| `guia.html` | Este mesmo guia em versão visual, com botão de idioma (português/inglês) e caixas que abrem explicando Colab, GPU T4 e o que acontece por trás. Duplo clique para abrir no navegador. |

Uso pelo PowerShell, se preferir a linha de comando:

```powershell
python3 mp4_para_mp3.py meu_video.mp4      # um arquivo
python3 mp4_para_mp3.py C:\videos          # uma pasta inteira
python3 mp4_para_mp3.py                    # tudo o que estiver na pasta atual
```

---

## Como as legendas são montadas

Um notebook é uma sequência de blocos de código chamados **células**, que rodam de cima para baixo.
`Executar tudo` roda as sete na ordem, sem você precisar clicar em cada uma:

| Célula | O quê |
|---|---|
| 1 | Confere a GPU e instala `faster-whisper` |
| 2 | Encontra (ou recebe) o `.mp3` |
| 3 | `large-v3`, `language="pt"`, `compute_type="float16"`, VAD ligado, timestamps por palavra, escada de tentativas até `1.0` — o `.mp3` vai direto para o modelo |
| 4 | Monta as legendas (máx. 2 linhas de 40 caracteres, entre 0,7 s e 6 s cada, **legenda 1 em `00:00:00,000`**) e já grava o **`_bruto.srt`** |
| 5 | Revisa o português com o Qwen3-8B, em blocos de 25 legendas — **só texto, nunca os horários** |
| 6 | Refaz a quebra de linhas, confere tudo de novo e grava o **`.srt` final** |
| 7 | Mostra o começo do `.srt` e dispara os dois downloads |

Para mudar o visual das legendas, mexa só nos valores do topo da célula 4:
`MAX_CHARS`, `MAX_LINHAS`, `MAX_DUR`, `MIN_DUR`, `GAP_QUEBRA`, `ESPERA_ANCORA`.
Para mexer na revisão, os valores ficam no topo da célula 5: `POLIR`, `LOTE`, `CONTEXTO`,
`CRESCIMENTO_MAX`.

**Por que a revisão não desalinha a legenda:** o modelo recebe uma lista de `{índice, texto}` e
tem que devolver a mesma lista, com os mesmos índices e a mesma quantidade. Os horários ficam
guardados no notebook e são recolados no fim. Se a resposta não bater exatamente, aquele bloco
inteiro volta ao texto original.

**Sobre a legenda 1:** ela começa em `00:00:00,000` para o arquivo nunca abrir com um vazio.
A exceção é quando o vídeo começa com vinheta ou música longa — aí a legenda 1 esperaria mais de
`ESPERA_ANCORA` segundos (6 s) até alguém falar, ficaria 20 s parada na tela e adiantaria a fala.
Nesse caso a legenda 1 espera a fala começar de verdade. É o que acontece no vídeo de `exemplo/`,
que abre com 14 s de vinheta.

O áudio sai mono, 16 kHz, 64 kbps — exatamente o formato que o Whisper usa por dentro.
É por isso que o `.mp3` fica pequeno sem perder qualidade de transcrição.

---

## Teste já executado (05/09/2026)

Rodado de ponta a ponta, com o notebook recém-enviado para o Colab e `Executar tudo`:

- ambiente: Tesla T4, `faster-whisper 1.2.1`, `ctranslate2 4.8.2`, CUDA disponível;
- **vídeo 1** — `exemplo/amostra_ptbr.mp4` (5 min 5 s, *"Consultor dá dicas para evitar
  superendividamento"*, Senado Federal / TV Senado): 49 segmentos em **22 s**, 673 palavras →
  **54 legendas**, primeira em `00:00:14,380` (o vídeo abre com vinheta), linha mais longa de
  42 caracteres, nenhuma sobreposição, nenhuma legenda acima de 6 s;
- **vídeo 2** — *"TV Senado inaugura canal digital no Maranhão"* (45 s): 6 segmentos em **4 s**,
  104 palavras → **10 legendas**, primeira em `00:00:00,000`;
- os dois `.srt` baixaram sozinhos pelo navegador.

> Esse teste é o registro daquele dia e o notebook mudou depois dele: a linha caiu de 42 para 40
> caracteres, o corte de silêncio do VAD subiu de 0,5 s para 2 s, e entrou a etapa de revisão.
> As duas primeiras coisas mudam onde as legendas quebram, então a contagem do `exemplo/` sai
> diferente de 54 — não é regressão.

## Teste da revisão (07/09/2026)

Mesmo vídeo, notebook atual, `Executar tudo` numa T4:

- 52 segmentos em **23 s**, 679 palavras → **58 legendas**, primeira em `00:00:14,380`;
- revisão: `llama-cpp-python` com CUDA ativo, `Qwen3-8B-Q4_K_M` (5,03 GB) carregado na mesma GPU,
  **3 blocos de legendas, nenhum descartado**, revisão inteira em **117 s**;
- comparando o `_bruto.srt` com o `.srt` final: 282 linhas nos dois, **nenhum horário diferente**
  e **uma linha de texto alterada** — `juro muito alto Procure` → `juro muito alto, procure`;
- os dois `.srt` baixaram sozinhos pelo navegador.

> Nessa mesma rodada o revisor tentou inventar vírgula no fim de outras 4 legendas; a guarda de
> pontuação descrita acima recusou as 4. Foi ela que fechou o teste — três versões do prompt não
> resolveram: proibir no texto deixava o modelo inerte (0 legendas tocadas) e reescrever o prompt
> em torno da tarefa fazia ele mover palavra de uma legenda para outra.

Vídeos de exemplo do Senado Federal / TV Senado, via Wikimedia Commons, licença **CC BY 3.0**
(o do `exemplo/` foi reencodado para MP4 apenas para servir de teste).

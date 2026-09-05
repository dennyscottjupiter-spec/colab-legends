# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é

Pipeline de duas máquinas que transforma um vídeo em legendas `.srt` em português: a conversão de áudio roda no PC local, a transcrição roda numa GPU grátis do Google Colab. **Não é um repositório git** — não há histórico, testes automatizados nem CI.

O README.md é escrito para o usuário final (não-programador) em português. Mudanças de comportamento precisam ser refletidas lá, principalmente nas tabelas "Se der problema" e "Como as legendas são montadas".

## Comandos

```powershell
python3 -m pip install imageio-ffmpeg   # única dependência local (setup, uma vez só)

python3 mp4_para_mp3.py meu_video.mp4   # converte um arquivo
python3 mp4_para_mp3.py C:\videos       # converte uma pasta
python3 mp4_para_mp3.py                 # converte tudo na pasta atual
```

`CONVERTER.cmd` é só um wrapper de duplo-clique / drag-and-drop: faz `cd /d "%~dp0"` e repassa `%*` para o script.

Verificação de ponta a ponta usa `exemplo/amostra_ptbr.mp4` (5 min): converter deve gerar um `.mp3` de ~2,4 MB idêntico em formato ao `exemplo/amostra_ptbr.mp3` já commitado. O `.srt` de referência tem 54 legendas, a primeira em `00:00:14,380` (o vídeo abre com 14 s de vinheta, então a âncora no zero não se aplica). Esse `.srt` foi gerado com `MAX_CHARS = 42` e `min_silence_duration_ms=500`; com a configuração atual (40 caracteres, silêncio de 2 s) a contagem de legendas muda — o que continua valendo como âncora é o timestamp da primeira legenda e os invariantes abaixo, não o número 54.

## Arquitetura

Três peças, duas máquinas, um único ponto de contato — o arquivo `.mp3`:

```
mp4_para_mp3.py  (PC local)          transcrever_ptbr_colab.ipynb  (Colab, GPU T4)
vídeo → mp3 mono 16 kHz 64 kbps  →   mp3 → large-v3 → .srt
```

**O contrato entre as duas metades é o formato do áudio**: mono, 16 kHz, 64 kbps. É exatamente o que o Whisper usa internamente, por isso o upload fica pequeno sem perder qualidade. O notebook não reconverte nada: o `faster-whisper` decodifica o `.mp3` com PyAV e já reamostra para 16 kHz mono por dentro (`decode_audio`), então o `ffmpeg` não entra do lado do Colab.

**O vídeo nunca sai do PC** — só o áudio sobe. Isso é uma promessa central do projeto, repetida no README e no notebook; qualquer mudança que faça um frame de vídeo subir para a nuvem quebra a premissa.

### `mp4_para_mp3.py`

`achar_ffmpeg()` tenta o `ffmpeg` do PATH e cai para o binário do pacote `imageio-ffmpeg` — é o que evita exigir instalação de programa pelo usuário. `converter()` pula silenciosamente arquivos que já têm `.mp3` ao lado, então rodar de novo é barato e idempotente.

### `transcrever_ptbr_colab.ipynb`

Uma célula de texto + cinco de código, projetadas para rodar em `Executar tudo` sem interação. Os metadados do `.ipynb` (`accelerator: GPU`, `colab.gpuType: T4`) já pedem a T4, então o usuário não precisa mexer no menu. Estado compartilhado via variáveis globais entre células: `ENTRADA` (célula 2) → `segmentos` (3) → `SRT` (4).

- **Célula 1** instala `faster-whisper==1.2.1` e `ctranslate2>=4.6.3`. O piso do `ctranslate2` é o que evita o crash histórico de cuDNN no Colab: a partir do 4.6.3 os wheels são compilados com `WITH_CUDNN=OFF` (Conv1d puro em CUDA), então `libcudnn_ops*.so` não pode mais faltar. Não instale `ffmpeg` aqui e não fixe `ctranslate2==4.4.0` (essa receita antiga reintroduz o bug).
- **Célula 2** prefere um `.mp3` já presente em `/content` (arrastado no painel *Arquivos*) e só chama `files.upload()` como fallback — o widget de upload é frágil e trava com arquivos grandes.
- **Célula 3** é a configuração de transcrição travada: `large-v3`, `language="pt"` (sem autodetecção), `device="cuda"`, `compute_type="float16"` (formato nativo da T4; `int8` só troca qualidade por VRAM que sobra), `word_timestamps=True` (obrigatório para as legendas curtas), `vad_filter=True` e `condition_on_previous_text=False` (ambos contra alucinação/loop do modelo). Não troque para `large-v3-turbo` — ele tem 4 camadas de decoder e os timestamps por palavra, que toda a célula 4 usa, ficam ruins. `modelo.transcribe()` devolve um gerador — o progresso só existe porque a célula itera manualmente.

  Três valores da célula 3 são contraintuitivos e não devem ser "simplificados":
  - **`temperature` tem que terminar em `1.0`.** A escada é uma cadeia de novas tentativas: cada degrau só roda se o anterior produziu texto suspeito. Se a lista acaba e a janela ainda falha, o `for…else` do `generate_with_fallback` **aceita o melhor dos fracassos** — o loop de repetição vai direto para o `.srt`. Encurtar a lista não economiza nada nas janelas boas (elas param em `0.0`), só remove as saídas de emergência.
  - **`min_silence_duration_ms=2000`** (padrão da lib; já esteve em 500). O Silero funde dois trechos de fala quando o intervalo entre eles é menor que `2 * speech_pad_ms` = 800 ms, e a pausa é **zerada** ao remontar o áudio. Com 500 ms, as pausas de 0,5 a 1,5 s desapareciam — exatamente as que o `GAP_QUEBRA = 0.7` da célula 4 existe para detectar. Menos fronteiras de corte também significa menos erro em `restore_speech_timestamps`.
  - **`speech_pad_ms=400`** é o padrão e não deve ser reduzido: com 200 ms o modelo cortava as primeiras palavras da fala.

  **Nunca ligue nesta célula** (todos degradam os timestamps por palavra ou são inertes aqui): `repetition_penalty` e `no_repeat_ngram_size` — penalizam palavras funcionais legítimas do português, o modelo troca palavra real por inventada e o alinhamento DTW desanda no resto da janela; `initial_prompt` — com `condition_on_previous_text=False` ele é descartado a partir da 2ª janela (`prompt_reset_since` é reatribuído a cada janela), então influencia 30 s de um áudio de 2 h e ainda pode vazar para o texto; `BatchedInferencePipeline` — força `temperature[:1]` (mata a escada acima), força `hallucination_silence_threshold=None`, e pica o áudio em pedaços de 30 s, multiplicando as fronteiras de VAD. `hotwords` é a exceção útil: persiste em todas as janelas, mas só vale como lista curta de termos próprios (nunca uma frase ou instrução).
- **Célula 4** é a lógica de legendagem, a única parte com regras de negócio reais. Fluxo: `coletar_palavras` (achata segmentos em palavras com tempo) → `agrupar` (quebra por largura de tela, `MAX_DUR` ou pausa `GAP_QUEBRA`) → `montar_legendas` (âncora no zero + remove sobreposição + limita duração) → `escrever_srt`. Os parâmetros de exibição (`MAX_CHARS`, `MAX_LINHAS`, `MAX_DUR`, `MIN_DUR`, `GAP_QUEBRA`, `ESPERA_ANCORA`) ficam no topo da célula e são o único lugar a mexer para mudar o visual.

## Invariantes das legendas

Regras que os `assert` no fim da célula 4 e o arquivo de exemplo protegem:

1. **A legenda 1 começa em `00:00:00,000`** quando a fala começa nos primeiros `ESPERA_ANCORA` segundos (`ancorar_no_zero=True`). Se o vídeo abre com vinheta/música longa, a âncora é abandonada — esticar a legenda 1 por 20 s dava spoiler e dessincronia. Há um `assert` condicional para isso.
2. **Sem sobreposição de tempo**: cada `ini` é empurrado para no mínimo o `fim` da legenda anterior.
3. **Duração entre `MIN_DUR` e `MAX_DUR`** por legenda, aplicada depois da âncora (`min`/`max` no fim de `montar_legendas`, com `assert` de garantia).
4. **Máximo 2 linhas de 40 caracteres** (`MAX_CHARS = 40`, `MAX_LINHAS = 2` — equivalem a `--max_line_width 40 --max_line_count 2` da linha de comando de referência); `quebrar_linhas()` procura o corte mais equilibrado e só cai na quebra gulosa se nenhum corte couber. Palavra maior que a linha inteira é fatiada por `_fatiar()`.

## Convenções

- Todo o texto voltado ao usuário — README, prints, mensagens de erro, docstrings, nomes de função e de variável — é em **português**. Mantenha assim.
- O código-fonte é **ASCII sem acentos** (`transcricao`, `nao`, `audio`) para não quebrar em consoles com codepage legado do Windows; só o README.md e as células markdown usam acentuação completa.
- `mp4_para_mp3.py` carrega um header de frontmatter em comentário no topo — se mudar exports ou dependências, atualize o header no mesmo edit.

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
vídeo → mp3 mono 16 kHz 64 kbps  →   mp3 → large-v3 → _bruto.srt → Qwen3-8B → .srt
```

**Saem dois arquivos.** `<nome>_bruto.srt` é gravado assim que as legendas ficam prontas (célula 4)
e `<nome>.srt` depois da revisão de português (célula 6). O bruto existe para que o usuário tenha
uma legenda completa mesmo se o LLM falhar ou o Colab cair no meio — não remova esse arquivo.

**O contrato entre as duas metades é o formato do áudio**: mono, 16 kHz, 64 kbps. É exatamente o que o Whisper usa internamente, por isso o upload fica pequeno sem perder qualidade. O notebook não reconverte nada: o `faster-whisper` decodifica o `.mp3` com PyAV e já reamostra para 16 kHz mono por dentro (`decode_audio`), então o `ffmpeg` não entra do lado do Colab.

**O vídeo nunca sai do PC** — só o áudio sobe. Isso é uma promessa central do projeto, repetida no README e no notebook; qualquer mudança que faça um frame de vídeo subir para a nuvem quebra a premissa.

### `mp4_para_mp3.py`

`achar_ffmpeg()` tenta o `ffmpeg` do PATH e cai para o binário do pacote `imageio-ffmpeg` — é o que evita exigir instalação de programa pelo usuário. `converter()` pula silenciosamente arquivos que já têm `.mp3` ao lado, então rodar de novo é barato e idempotente.

### `transcrever_ptbr_colab.ipynb`

Uma célula de texto + sete de código, projetadas para rodar em `Executar tudo` sem interação. Os metadados do `.ipynb` (`accelerator: GPU`, `colab.gpuType: T4`) já pedem a T4, então o usuário não precisa mexer no menu. Estado compartilhado via variáveis globais entre células: `ENTRADA` (célula 2) → `segmentos` (3) → `legendas` + `TEXTO_BRUTO` + `SRT_BRUTO` (4) → `legendas` revisadas (5) → `SRT` (6).

- **Célula 1** instala `faster-whisper==1.2.1` e `ctranslate2>=4.6.3`. O piso do `ctranslate2` é o que evita o crash histórico de cuDNN no Colab: a partir do 4.6.3 os wheels são compilados com `WITH_CUDNN=OFF` (Conv1d puro em CUDA), então `libcudnn_ops*.so` não pode mais faltar. Não instale `ffmpeg` aqui e não fixe `ctranslate2==4.4.0` (essa receita antiga reintroduz o bug).
- **Célula 2** prefere um `.mp3` já presente em `/content` (arrastado no painel *Arquivos*) e só chama `files.upload()` como fallback — o widget de upload é frágil e trava com arquivos grandes.
- **Célula 3** é a configuração de transcrição travada: `large-v3`, `language="pt"` (sem autodetecção), `device="cuda"`, `compute_type="float16"` (formato nativo da T4; `int8` só troca qualidade por VRAM que sobra), `word_timestamps=True` (obrigatório para as legendas curtas), `vad_filter=True` e `condition_on_previous_text=False` (ambos contra alucinação/loop do modelo). Não troque para `large-v3-turbo` — ele tem 4 camadas de decoder e os timestamps por palavra, que toda a célula 4 usa, ficam ruins. `modelo.transcribe()` devolve um gerador — o progresso só existe porque a célula itera manualmente.

  Três valores da célula 3 são contraintuitivos e não devem ser "simplificados":
  - **`temperature` tem que terminar em `1.0`.** A escada é uma cadeia de novas tentativas: cada degrau só roda se o anterior produziu texto suspeito. Se a lista acaba e a janela ainda falha, o `for…else` do `generate_with_fallback` **aceita o melhor dos fracassos** — o loop de repetição vai direto para o `.srt`. Encurtar a lista não economiza nada nas janelas boas (elas param em `0.0`), só remove as saídas de emergência.
  - **`min_silence_duration_ms=2000`** (padrão da lib; já esteve em 500). O Silero funde dois trechos de fala quando o intervalo entre eles é menor que `2 * speech_pad_ms` = 800 ms, e a pausa é **zerada** ao remontar o áudio. Com 500 ms, as pausas de 0,5 a 1,5 s desapareciam — exatamente as que o `GAP_QUEBRA = 0.7` da célula 4 existe para detectar. Menos fronteiras de corte também significa menos erro em `restore_speech_timestamps`.
  - **`speech_pad_ms=400`** é o padrão e não deve ser reduzido: com 200 ms o modelo cortava as primeiras palavras da fala.

  **Nunca ligue nesta célula** (todos degradam os timestamps por palavra ou são inertes aqui): `repetition_penalty` e `no_repeat_ngram_size` — penalizam palavras funcionais legítimas do português, o modelo troca palavra real por inventada e o alinhamento DTW desanda no resto da janela; `initial_prompt` — com `condition_on_previous_text=False` ele é descartado a partir da 2ª janela (`prompt_reset_since` é reatribuído a cada janela), então influencia 30 s de um áudio de 2 h e ainda pode vazar para o texto; `BatchedInferencePipeline` — força `temperature[:1]` (mata a escada acima), força `hallucination_silence_threshold=None`, e pica o áudio em pedaços de 30 s, multiplicando as fronteiras de VAD. `hotwords` é a exceção útil: persiste em todas as janelas, mas só vale como lista curta de termos próprios (nunca uma frase ou instrução).
- **Célula 4** é a lógica de legendagem, a única parte com regras de negócio reais. Fluxo: `coletar_palavras` (achata segmentos em palavras com tempo) → `agrupar` (quebra por largura de tela, `MAX_DUR` ou pausa `GAP_QUEBRA`) → `montar_legendas` (âncora no zero + remove sobreposição + limita duração) → `conferir_invariantes` → `escrever_srt` no `_bruto.srt`. Os parâmetros de exibição (`MAX_CHARS`, `MAX_LINHAS`, `MAX_DUR`, `MIN_DUR`, `GAP_QUEBRA`, `ESPERA_ANCORA`) ficam no topo da célula e são o único lugar a mexer para mudar o visual. `TEXTO_BRUTO` guarda uma cópia dos textos crus — é o que permite re-executar a célula 5 sem revisar o que já foi revisado.
- **Célula 5** é a revisão de português, opcional (`POLIR = True` no topo). Roda **sobre a lista de legendas pronta**, nunca sobre os segmentos da célula 3 — mexer no texto antes de `agrupar` destruiria os timestamps por palavra. Depois dela a célula 6 refaz `quebrar_linhas`, então o limite de tela continua valendo.

  - **Runtime:** `llama-cpp-python` + `Qwen/Qwen3-8B-GGUF` (`Qwen3-8B-Q4_K_M.gguf`, ~5 GB). O wheel vem do **release no GitHub** (`v0.3.35-cu124`, `py3-none-manylinux_2_35_x86_64`), não do índice `abetlen.github.io/whl/cu124`: aquele índice para no `cp312` e o Colab passou a rodar **Python 3.13**, então o pip ignora o wheel, baixa o sdist e começa a compilar do fonte — 20+ min e sem CUDA no fim. O wheel do release é `py3-none` porque a biblioteca entra por `ctypes`, então serve para qualquer Python 3. `llama_supports_gpu_offload()` é checado logo depois do import justamente para não rodar na CPU sem ninguém perceber.
  - **Antes de carregar**, solta o whisper da VRAM: `del modelo` + `gc.collect()` + `torch.cuda.empty_cache()`.
  - **Contrato:** o modelo nunca vê nem devolve timestamp. Recebe lotes de `LOTE = 25` legendas como `[{"i": int, "t": str}]`, mais as `CONTEXTO = 3` anteriores em um campo separado, só de leitura. O JSON de volta é forçado pela gramática GBNF nativa do llama.cpp (`response_format={"type": "json_object", "schema": ESQUEMA}`). O esquema é chapado de propósito (só `integer` e `string`): a conversão JSON-Schema→GBNF quebra com atalhos de regex tipo `\d`, `\w`, `\s`.
  - **`repeat_penalty=1.0` é obrigatório.** O padrão da lib é 1.1 e penalizaria as chaves `"i"`/`"t"`, que se repetem 25 vezes no JSON.
  - **Modo de raciocínio desligado** com `/no_think` no início do prompt de sistema: um bloco `<think>` quebraria a leitura do JSON.
  - **Validação em duas camadas.** Por lote (descarta tudo e refaz uma vez com `temperature=0.3`, depois desiste e fica com o original): JSON ilegível, contagem diferente, ou conjunto de índices diferente. Por legenda, em `_aceitar(velho, novo, proximo)` (mantém só aquela no original): texto vazio, crescimento acima de `CRESCIMENTO_MAX = 1.3`, texto que não passa em `cabe()`, ou pontuação de `PONTO_FIM` inventada no fim quando `proximo` começa em minúscula. A camada por legenda é o que garante o invariante 4 depois da revisão.
  - **A guarda de pontuação não é opcional, e não dá para trocá-la por prompt.** Numa T4 o modelo acerta o caso de duas frases coladas na mesma legenda e, no mesmo lote, fecha com vírgula quatro legendas que são só um pedaço de frase (`"ela se torna,"`, `"que privilegie,"`). Três versões do prompt foram testadas na GPU: proibir a pontuação no fim deixa o modelo inerte (0 de 58 legendas tocadas); reescrever o prompt com a tarefa na frente faz ele mover palavra de uma legenda para outra e invalidar o lote (2 de 3 lotes descartados, e 3 de 6 com `LOTE = 10`). O `proximo` vem de `TEXTO_BRUTO[i + 1]`, não da lista revisada, porque as legendas mudam durante o laço.
  - **O prompt (`REGRAS`) é o único texto acentuado do projeto**, de propósito: é material linguístico para o modelo, não saída de console. Escrever "pontuacao" ali seria ensinar ao revisor exatamente o erro que ele tem que corrigir.
- **Célula 6** refaz `quebrar_linhas` (dentro de `escrever_srt`), chama `conferir_invariantes` de novo e grava o `.srt` final.

## Invariantes das legendas

Regras que `conferir_invariantes()` protege. Ela roda **duas vezes**: na célula 4 (antes de gravar o `_bruto.srt`) e na célula 6 (depois da revisão, antes de gravar o `.srt` final). Os invariantes 1 a 3 são de tempo e a revisão não pode quebrá-los por construção — os timestamps nunca saem do notebook (verificado na T4: `_bruto.srt` e `.srt` final saíram com 282 linhas e nenhum horário diferente). O invariante 4 é o único que a revisão põe em risco, e é por isso que `_aceitar()` recusa qualquer texto revisado que não caiba na tela.

1. **A legenda 1 começa em `00:00:00,000`** quando a fala começa nos primeiros `ESPERA_ANCORA` segundos (`ancorar_no_zero=True`). Se o vídeo abre com vinheta/música longa, a âncora é abandonada — esticar a legenda 1 por 20 s dava spoiler e dessincronia. Há um `assert` condicional para isso.
2. **Sem sobreposição de tempo**: cada `ini` é empurrado para no mínimo o `fim` da legenda anterior.
3. **Duração entre `MIN_DUR` e `MAX_DUR`** por legenda, aplicada depois da âncora (`min`/`max` no fim de `montar_legendas`, com `assert` de garantia).
4. **Máximo 2 linhas de 40 caracteres** (`MAX_CHARS = 40`, `MAX_LINHAS = 2` — equivalem a `--max_line_width 40 --max_line_count 2` da linha de comando de referência); `quebrar_linhas()` procura o corte mais equilibrado e só cai na quebra gulosa se nenhum corte couber. Palavra maior que a linha inteira é fatiada por `_fatiar()`.

## Convenções

- Todo o texto voltado ao usuário — README, prints, mensagens de erro, docstrings, nomes de função e de variável — é em **português**. Mantenha assim.
- O código-fonte é **ASCII sem acentos** (`transcricao`, `nao`, `audio`) para não quebrar em consoles com codepage legado do Windows; as exceções são o README.md, as células markdown e a constante `REGRAS` da célula 5 (prompt do LLM, ver acima).
- `mp4_para_mp3.py` carrega um header de frontmatter em comentário no topo — se mudar exports ou dependências, atualize o header no mesmo edit.

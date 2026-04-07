# Arquitetura

## Visao geral

O projeto esta organizado em um pacote Python simples com uma CLI fina e um modulo central que concentra descoberta, comparacao, persistencia de estado e geracao de relatorios.

## Modulos

### `discografia_app.py`

- wrapper de compatibilidade
- importa `main` de `discografia.cli`
- permite manter o fluxo antigo de execucao

### `discografia/cli.py`

- resolve o caminho raiz
- define o parser de argumentos
- despacha para `run`, `resume`, `pause`, `cancel` e `status`

### `discografia/core.py`

Responsavel por:

- normalizacao de nomes
- descoberta de pastas com audio
- parsing local de arquivos
- consulta HTTP ao Apple Music
- heuristica de comparacao
- geracao do markdown final
- persistencia do estado e progresso
- controle de pausa e cancelamento

## Modelo de dados

As estruturas principais em `discografia/core.py` sao:

- `LocalTrack`: representa uma faixa local inferida do nome do arquivo
- `LocalAlbum`: representa um agrupamento local de album
- `PublicRelease`: representa um lancamento publico encontrado
- `AlbumAssessment`: representa o resultado da comparacao entre local e publico
- `AppContext`: encapsula caminhos de estado, log e progresso

## Fluxo de processamento

1. `process_run()` carrega ou recria o estado.
2. `refresh_queue()` descobre os artistas a processar.
3. `parse_local_albums()` infera artista, album, faixa e lacunas de numeracao.
4. `fetch_apple_music_catalog()` busca o artista e seus lancamentos publicos.
5. `assess_catalog()` compara o acervo local com o publico.
6. `build_markdown()` monta o relatorio por artista.
7. `write_progress()` atualiza o progresso humano.
8. `save_state()` persiste o estado de maquina.

## Heuristica de comparacao

O algoritmo privilegia seguranca e nao agressividade.

- usa normalizacao ASCII
- compara titulos com `SequenceMatcher`
- simplifica titulos para separar nucleo de edicoes
- penaliza divergencias como `playback`, `karaoke`, `instrumental`, `ao vivo` e `acustico`
- evita tratar `playback` como ausente principal quando o acervo local nao aponta para isso
- considera contagem de faixas antes de marcar um album como presente

## Persistencia

Arquivos usados em cada raiz processada:

- `.discografia/state.json`
- `.discografia/control.json`
- `.discografia/discografia.log`
- `PROGRESSO_MUSICAS_FALTANTES.md`

## Ponto de seguranca operacional

O processamento foi desenhado para interromper entre artistas, nao no meio de um artista. Isso reduz risco de relatorio parcialmente gravado e simplifica retomada.

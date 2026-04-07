# Discografia Rules

## Continuidade

- Este projeto usa `PROGRESSO_MUSICAS_FALTANTES.md` como marcador canonico de retomada.
- Antes de iniciar qualquer novo artista, leia `PROGRESSO_MUSICAS_FALTANTES.md` para identificar o ultimo concluido e o proximo da fila.
- Ao concluir um arquivo `*_musicas_faltantes.md`, atualize `PROGRESSO_MUSICAS_FALTANTES.md` na mesma tarefa.
- Em caso de travamento ou perda de contexto, reconstrua o ponto de retomada primeiro por `PROGRESSO_MUSICAS_FALTANTES.md` e depois confirme pelos timestamps dos `.md` mais recentes.

## Padrao do lote

- Cada arquivo deve registrar comparacao entre a pasta local em `C:\Users\jairs\Music\Gospel\...` e o catalogo publico do artista no Apple Music.
- Manter texto em ASCII simples, seguindo o formato ja usado no lote: resumo, albuns presentes, faltantes parciais quando houver, lancamentos ausentes, observacao e fontes.
- Ignorar `playback` como criterio principal de faltantes, salvo quando isso for relevante para esclarecer a comparacao.

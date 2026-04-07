# Regras do aplicativo Discografia

## Objetivo

Automatizar a analise de pastas musicais para gerar arquivos `*_musicas_faltantes.md`, comparando o acervo local com o catalogo publico do artista no Apple Music, com retomada segura entre execucoes.

## Relacao com AGENTS

- `AGENTS.md` deste projeto concentra as instrucoes operacionais para o agente durante a execucao do trabalho.
- Este arquivo concentra as regras funcionais e de comportamento do aplicativo.
- Em caso de sobreposicao, trate `AGENTS.md` como guia operacional do agente e este arquivo como especificacao funcional do projeto.

## Escopo padrao

- funciona a partir da pasta atual ou de uma raiz informada por parametro
- varre a raiz informada e subpastas relevantes
- consegue operar em execucoes futuras sem depender de memoria conversacional

## Entrada

- execucao sem parametros
- execucao com caminho absoluto ou relativo
- comandos `run`, `resume`, `pause`, `cancel` e `status`

## Saida esperada

- um markdown por artista no formato `*_musicas_faltantes.md`
- progresso humano em `PROGRESSO_MUSICAS_FALTANTES.md`
- estado interno em `.discografia/state.json`
- sinalizacao externa em `.discografia/control.json`
- log em `.discografia/discografia.log`

## Fonte canonica de continuidade

- `PROGRESSO_MUSICAS_FALTANTES.md` e a referencia humana primaria
- `state.json` e a referencia de maquina para continuidade
- divergencias devem ser toleradas sem corromper o processamento

## Modus operandi

1. Resolver a raiz de trabalho.
2. Descobrir pastas com arquivos de audio.
3. Ordenar artistas por nome normalizado.
4. Processar um artista por vez.
5. Inferir albums e faixas a partir dos nomes dos arquivos.
6. Consultar o catalogo publico do Apple Music.
7. Comparar local x publico com criterio conservador.
8. Gerar ou atualizar o markdown do artista.
9. Atualizar imediatamente o progresso humano e o estado de maquina.

## Regras de comparacao

- priorizar comparacao entre a pasta local e o catalogo publico do artista
- manter texto em ASCII simples
- nao inferir discografia completa por semelhanca fraca
- quando houver divergencia de titulo, edicao ou contagem, registrar como parcial
- `playback`, `karaoke` e `instrumental` nao devem servir como match principal por padrao
- `ao vivo` e `acustico` devem influenciar a confianca da comparacao

## Regras de seguranca operacional

- nao pedir confirmacao por lote
- persistir estado frequentemente
- permitir cancelamento limpo
- permitir pausa com continuidade exata do ultimo ponto seguro
- considerar o limite operacional entre artistas, nao no meio do artista

## Estado e retomada

O estado minimo precisa manter:

- raiz atual de trabalho
- fila calculada
- indice da fila
- artista atual
- ultimo artista concluido
- ultimo arquivo concluido
- proximo artista
- lista recente de concluidos
- data e hora da ultima atualizacao
- `status`: `idle`, `rodando`, `pausado`, `cancelado`, `erro` ou `concluido`
- erros recentes

## Comportamento quando a fila terminar

- atualizar `PROGRESSO_MUSICAS_FALTANTES.md` com `fim da fila atual`
- marcar estado interno como `concluido`
- permitir nova execucao futura na mesma raiz ou em outra raiz

## Implementacao atual

- linguagem: Python
- empacotamento: PyInstaller
- consulta publica: endpoints publicos do iTunes/Apple Music
- interface operacional: linha de comando

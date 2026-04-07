# Regras do aplicativo Discografia

## Objetivo

Este aplicativo deve automatizar a rotina de analise de pastas musicais para gerar arquivos `*_musicas_faltantes.md`, comparando o acervo local com o catalogo publico do artista no Apple Music, seguindo o padrao consolidado neste workspace.

## Escopo padrao

- O aplicativo deve funcionar a partir da pasta onde estiver sendo executado.
- Quando nenhum parametro for informado, deve usar como raiz de varredura a pasta atual.
- Quando uma nova pasta for informada por parametro, deve usar essa pasta como raiz de varredura.
- A varredura deve incluir a raiz informada e todas as subpastas relevantes.
- O aplicativo deve conseguir operar novamente em qualquer data futura, sem depender desta conversa.

## Entrada

- Aceitar execucao sem parametros.
- Aceitar um parametro de caminho, absoluto ou relativo.
- Aceitar retomada automatica a partir de estado salvo.
- Aceitar comandos de pausa, cancelamento e retomada.

## Saida esperada

- Gerar um arquivo markdown por artista, no formato `*_musicas_faltantes.md`.
- Manter um marcador canonico de progresso em `PROGRESSO_MUSICAS_FALTANTES.md`.
- Registrar um estado interno proprio do aplicativo para pausa, cancelamento e continuidade.
- Produzir logs suficientes para auditoria e retomada segura.

## Fonte canonica de continuidade

- O arquivo `PROGRESSO_MUSICAS_FALTANTES.md` continua sendo o marcador canonico humano de retomada.
- O aplicativo deve manter tambem um arquivo de estado de maquina para retomar execucao interrompida.
- Em caso de divergencia, o aplicativo deve preservar os dois e registrar alerta no log.

## Modus operandi

1. Ler `PROGRESSO_MUSICAS_FALTANTES.md`, se existir.
2. Identificar o ultimo arquivo concluido e o ponto atual de retomada.
3. Descobrir as pastas de artistas dentro da raiz escolhida.
4. Ordenar as pastas por nome, em ordem alfabetica pratica.
5. Determinar a fila restante com base no progresso existente ou iniciar fila nova quando necessario.
6. Processar em lotes prudentes, sem sobrecarregar o sistema.
7. Para cada artista:
   - ler os arquivos locais da pasta
   - identificar albums, faixas, sequencias e lacunas
   - consultar o catalogo publico do artista no Apple Music
   - comparar com criterio conservador
   - gerar ou atualizar o markdown do artista
   - atualizar imediatamente `PROGRESSO_MUSICAS_FALTANTES.md`
   - salvar estado interno apos cada artista
8. Ao fim da fila, registrar que a fila atual terminou.

## Regras de comparacao

- Priorizar comparacao entre a pasta local e o catalogo publico do artista no Apple Music.
- Manter texto em ASCII simples.
- Seguir o formato consolidado no lote:
  - titulo
  - contexto da comparacao
  - resumo
  - albums presentes
  - faltantes parciais, quando houver
  - lancamentos ausentes
  - observacao
  - fontes
- Ignorar `playback` como criterio principal de faltantes, salvo quando isso esclarecer a comparacao.
- Quando a correspondencia publica nao for segura, usar modo conservador.
- Nao inferir discografia completa apenas por semelhanca fraca de nome.
- Quando houver divergencia de edicao, contagem ou titulo, registrar como parcial ou edicao diferente.

## Regras de seguranca operacional

- Nao pedir confirmacao manual a cada bloco fixo de pastas.
- Ajustar o tamanho do lote dinamicamente de forma prudente.
- Reduzir paralelismo quando o sistema estiver sob carga ou quando a escrita ficar pesada.
- Persistir estado frequente para minimizar retrabalho.
- Permitir cancelamento limpo sem corromper arquivos ja concluidos.
- Permitir pausa com continuidade exata do ponto salvo.

## Estado e retomada

O aplicativo deve manter estado minimo com:

- raiz atual de trabalho
- fila calculada
- artista atual
- ultimo artista concluido
- lista recente de concluidos
- data e hora da ultima atualizacao
- status da execucao: `rodando`, `pausado`, `cancelado`, `concluido`
- configuracao de lote e limites operacionais
- erros e alertas relevantes

## Estrutura dos markdowns por artista

Cada arquivo deve preservar o padrao abaixo, ajustado ao caso real:

- `# Nome do artista - musicas faltantes`
- data da comparacao
- caminho local analisado
- referencia ao Apple Music
- `## Resumo`
- `## Albums que parecem presentes na pasta`
- `## Faltantes parciais ou com divergencia`, quando aplicavel
- `## Lancamentos ausentes da pasta`, quando aplicavel
- `## Observacao`
- `## Fontes`

## Comportamento quando a fila terminar

- Atualizar `PROGRESSO_MUSICAS_FALTANTES.md` indicando `fim da fila atual`.
- Manter estado interno consistente como `concluido`.
- Permitir nova execucao futura na mesma raiz ou em outra raiz.

## Requisitos do executavel

- Deve ser executavel por linha de comando.
- Deve funcionar a partir da pasta onde estiver localizado.
- Deve aceitar uma nova pasta por parametro.
- Deve recriar o fluxo deste workspace sem depender de memoria conversacional.
- Deve ser robusto contra interrupcao.
- Deve ser capaz de continuar de onde cancelou.

## Pendencias de implementacao

- definir linguagem e formato do executavel
- definir estrategia de consulta ao Apple Music
- definir layout dos arquivos de estado e log
- definir heuristica de lote prudente
- definir interface de pausa, cancelamento e retomada

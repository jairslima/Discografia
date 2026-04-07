# Operacao

## Formas de executar

### Sem parametros

Processa a pasta atual:

```powershell
discografia.cmd
```

### Com raiz explicita

```powershell
discografia.cmd run "D:\Musicas\Gospel"
```

### Retomar

```powershell
discografia.cmd resume "D:\Musicas\Gospel"
```

### Pausar

```powershell
discografia.cmd pause "D:\Musicas\Gospel"
```

### Cancelar

```powershell
discografia.cmd cancel "D:\Musicas\Gospel"
```

### Ver estado

```powershell
discografia.cmd status "D:\Musicas\Gospel"
```

## O que esperar na pasta de saida

- um arquivo `*_musicas_faltantes.md` por artista processado
- um `PROGRESSO_MUSICAS_FALTANTES.md`
- uma pasta `.discografia/` com estado, log e controle

## Interpretacao do relatorio por artista

### `## Resumo`

Traz contagem total do que foi avaliado localmente e publicamente.

### `## Inventario local`

Lista albums inferidos localmente e mostra:

- quantidade de faixas
- numeros de faixa encontrados
- lacunas de numeracao, quando houver

### `## Albums que parecem presentes na pasta`

Usado quando titulo e contagem de faixas ficam suficientemente alinhados.

### `## Faltantes parciais ou com divergencia`

Usado quando:

- ha album local sem correspondencia publica segura
- o titulo sugere mesma obra, mas com edicao diferente
- a contagem de faixas diverge

### `## Lancamentos ausentes da pasta`

Lista o que aparece no catalogo publico e nao foi encontrado com seguranca no acervo local.

### `## Fontes`

Registra notas da consulta publica e URLs de Apple Music quando disponiveis.

## Estado operacional

O `PROGRESSO_MUSICAS_FALTANTES.md` e a referencia humana principal.

O `state.json` e a referencia de maquina para:

- `status`
- indice da fila
- ultimo artista concluido
- proximo artista
- erros recentes

## Limites conhecidos

- a inferencia local depende do padrao do nome do arquivo
- nao ha leitura de tags ID3
- a fonte publica usada e o catalogo visivel do Apple Music
- a comparacao e conservadora e pode preferir marcar divergencia a assumir equivalencia

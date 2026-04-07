# Discografia

Utilitario para gerar arquivos `*_musicas_faltantes.md` com pausa, cancelamento, retomada e comparacao conservadora entre o acervo local e o catalogo publico do Apple Music.

## Estrutura

- `discografia_app.py`: wrapper compativel com o fluxo anterior
- `discografia/cli.py`: entrada de linha de comando
- `discografia/core.py`: descoberta, comparacao, estado e geracao dos markdowns
- `tests/test_discografia.py`: verificacao automatizada minima do fluxo
- `build.ps1`: empacotamento com PyInstaller
- `discografia.cmd`: launcher que prefere o executavel em `dist/`

## Uso rapido

- executavel standalone:
  - `Discografia\dist\discografia\discografia.exe`
- executar na pasta atual:
  - `discografia.cmd`
- executar na pasta atual via Python:
  - `python discografia_app.py`
- executar em outra pasta:
  - `discografia.cmd run "D:\Musicas\Gospel"`
- retomar:
  - `discografia.cmd resume "D:\Musicas\Gospel"`
- pausar:
  - `discografia.cmd pause "D:\Musicas\Gospel"`
- cancelar:
  - `discografia.cmd cancel "D:\Musicas\Gospel"`
- ver estado:
  - `discografia.cmd status "D:\Musicas\Gospel"`

## Arquivos gerados

Na raiz analisada, o aplicativo grava:

- `*_musicas_faltantes.md`
- `PROGRESSO_MUSICAS_FALTANTES.md`
- `.discografia\state.json`
- `.discografia\control.json`
- `.discografia\discografia.log`

## Relatorio gerado

Cada markdown por artista agora inclui:

- resumo com contagens locais e publicas
- inventario local com lacunas de numeracao quando houver
- albums presentes com maior confianca
- divergencias parciais por titulo, edicao ou contagem
- lancamentos ausentes filtrando `playback`, `karaoke` e `instrumental` como criterio principal
- fontes e notas da consulta publica

## Desenvolvimento

- validar sintaxe:
  - `python -m py_compile discografia_app.py discografia\__init__.py discografia\cli.py discografia\core.py`
- rodar testes:
  - `python -m unittest discover -s tests -v`
- empacotar:
  - `.\build.ps1`

## Observacoes

- Sem parametro, a raiz analisada e a pasta atual.
- Quando uma pasta e passada por parametro, os arquivos de saida ficam nela.
- `discografia.cmd` prefere `dist\discografia\discografia.exe` quando ele existir.
- `pause` e `cancel` gravam um sinal; a execucao corrente aplica isso no proximo ponto seguro entre artistas.
- A comparacao continua conservadora: semelhanca fraca de titulo nao fecha equivalencia automaticamente.

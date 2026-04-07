# Discografia

Aplicativo de linha de comando para auditar um acervo musical local por artista, comparar esse acervo com o catalogo publico do Apple Music e gerar relatorios `*_musicas_faltantes.md` com continuidade segura entre execucoes.

O projeto esta publicado publicamente em:

- `https://github.com/jairslima/Discografia`

## Licenca

Este projeto usa licenca MIT.

- arquivo local: `LICENSE`

## O que o aplicativo faz

- descobre pastas de artistas com arquivos de audio
- identifica agrupamentos locais de album e faixas por heuristica de nome
- consulta o catalogo publico do Apple Music via endpoints publicos do iTunes
- compara o acervo local com criterio conservador
- gera um markdown por artista com presentes, divergencias e ausencias provaveis
- persiste estado, progresso humano e sinais de controle para pausa, retomada e cancelamento

## Comandos

Os comandos aceitos pela CLI sao:

- `run`
- `resume`
- `pause`
- `cancel`
- `status`

Exemplos:

```powershell
discografia.cmd
discografia.cmd run "D:\Musicas\Gospel"
discografia.cmd resume "D:\Musicas\Gospel"
discografia.cmd pause "D:\Musicas\Gospel"
discografia.cmd cancel "D:\Musicas\Gospel"
discografia.cmd status "D:\Musicas\Gospel"
python discografia_app.py run "D:\Musicas\Gospel"
```

## Como funciona

1. Resolve a raiz a ser processada.
2. Descobre subpastas com arquivos de audio.
3. Ordena a fila por nome de pasta normalizado.
4. Para cada artista, analisa nomes de arquivos para inferir album e faixa.
5. Consulta o Apple Music para localizar o artista e seus lancamentos publicos.
6. Compara local x publico com heuristica conservadora.
7. Gera `*_musicas_faltantes.md`.
8. Atualiza `PROGRESSO_MUSICAS_FALTANTES.md`, `state.json` e `discografia.log`.

## Saidas geradas

Na raiz analisada, o aplicativo grava:

- `*_musicas_faltantes.md`
- `PROGRESSO_MUSICAS_FALTANTES.md`
- `.discografia/state.json`
- `.discografia/control.json`
- `.discografia/discografia.log`

## Estrutura do projeto

- `discografia_app.py`: wrapper simples para manter compatibilidade com o fluxo antigo
- `discografia/cli.py`: parsing da CLI e despacho de comandos
- `discografia/core.py`: nucleo do aplicativo
- `discografia.cmd`: launcher Windows que prefere o executavel em `dist/`
- `build.ps1`: build com PyInstaller
- `pyproject.toml`: metadados do pacote e script `discografia`
- `tests/test_discografia.py`: testes automatizados
- `REGRAS_DISCOGRAFIA.md`: especificacao funcional consolidada

## Arquivos de documentacao

- `README.md`: visao geral e onboarding rapido
- `REGRAS_DISCOGRAFIA.md`: requisitos e regras do dominio
- `docs/ARQUITETURA.md`: desenho interno do aplicativo
- `docs/OPERACAO.md`: uso operacional e interpretacao das saidas
- `docs/DESENVOLVIMENTO.md`: manutencao, testes e build
- `docs/PUBLICACAO.md`: Git, GitHub e publicacao

## Instalacao e execucao

Requisitos:

- Windows com PowerShell
- Python 3.12+
- opcionalmente PyInstaller para gerar executavel

Execucao direta:

```powershell
python discografia_app.py
```

Execucao via launcher:

```powershell
discografia.cmd
```

Execucao via entrypoint do pacote:

```powershell
python -m discografia.cli run "D:\Musicas\Gospel"
```

## Desenvolvimento

Validar sintaxe:

```powershell
python -m py_compile discografia_app.py discografia\__init__.py discografia\cli.py discografia\core.py tests\test_discografia.py
```

Rodar testes:

```powershell
python -m unittest discover -s tests -v
```

Gerar executavel:

```powershell
.\build.ps1
```

## Observacoes importantes

- O aplicativo usa ASCII simples nos relatórios gerados.
- A comparacao e propositalmente conservadora.
- `playback`, `karaoke` e `instrumental` nao entram como pareamento principal por padrao.
- `pause` e `cancel` sao aplicados no proximo ponto seguro entre artistas.
- `run` reinicia a fila a partir da raiz informada.
- `resume` aproveita o estado salvo.

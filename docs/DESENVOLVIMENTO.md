# Desenvolvimento

## Requisitos

- Python 3.12+
- PowerShell
- opcionalmente PyInstaller

## Comandos de manutencao

### Validar sintaxe

```powershell
python -m py_compile discografia_app.py discografia\__init__.py discografia\cli.py discografia\core.py tests\test_discografia.py
```

### Rodar testes

```powershell
python -m unittest discover -s tests -v
```

### Gerar executavel

```powershell
.\build.ps1
```

## Estrategia de testes atual

Os testes em `tests/test_discografia.py` validam:

- sanitizacao do nome do artista
- deteccao de lacunas de numeracao de faixas
- filtro de `playback` na analise de ausencias
- fluxo minimo de `process_run()` com catalogo publico mockado

## Criterios para alterar heuristica

Ao mexer em comparacao:

- prefira falsos negativos a falsos positivos
- nao trate edicoes especiais como equivalencia automatica
- nao use `playback` como match principal salvo quando o local tambem indicar isso
- preserve a saida em ASCII simples

## Build

O build atual usa:

- `build.ps1`
- `PyInstaller`

Comando principal:

```powershell
python -m PyInstaller --noconfirm --clean --name discografia discografia_app.py
```

## Git

Fluxo minimo recomendado:

```powershell
git status
git add -A
git commit -m "Mensagem objetiva"
git push origin main
```

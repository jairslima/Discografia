# Publicacao

## Repositorio publico

Repositorio atual:

- `https://github.com/jairslima/Discografia`

## Licenca

O projeto foi publicado com licenca MIT.

Arquivo:

- `LICENSE`

## Estrategia de publicacao adotada

1. adicionar `LICENSE`
2. adicionar `.gitignore`
3. inicializar Git local
4. criar commit inicial
5. criar repositorio publico com GitHub CLI
6. fazer push de `main`
7. limpar artefatos de amostra do repositorio publico

## Itens que ficam fora do versionamento

Itens ignorados por `.gitignore`:

- `build/`
- `dist/`
- `__pycache__/`
- `_teste/`
- `.discografia/`
- diretorios temporarios `tmp*/` e `_tmp_test_*/`

## Publicar atualizacoes futuras

```powershell
git status
git add -A
git commit -m "Sua mensagem"
git push origin main
```

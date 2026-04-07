from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


AUDIO_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".wav",
    ".m4a",
    ".aac",
    ".ogg",
    ".wma",
    ".opus",
    ".alac",
}

STATE_DIRNAME = ".discografia"
STATE_FILENAME = "state.json"
CONTROL_FILENAME = "control.json"
LOG_FILENAME = "discografia.log"
PROGRESS_FILENAME = "PROGRESSO_MUSICAS_FALTANTES.md"
QUALIFIER_WORDS = {
    "ao",
    "vivo",
    "live",
    "playback",
    "karaoke",
    "instrumental",
    "remaster",
    "remastered",
    "deluxe",
    "expanded",
    "edition",
    "edicao",
    "version",
    "versao",
    "bonus",
    "track",
}


def utc_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def format_date_for_md() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def ensure_ascii_text(value: str) -> str:
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")


def ascii_slug(value: str) -> str:
    cleaned = ensure_ascii_text(value).lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned).strip("_")
    return cleaned or "artista"


def normalize(value: str) -> str:
    cleaned = ensure_ascii_text(value).lower()
    cleaned = cleaned.replace("&", "e")
    cleaned = re.sub(r"\bfeat\b|\bfeaturing\b|\bft\b", " ", cleaned)
    cleaned = re.sub(r"\([^)]*\)", " ", cleaned)
    cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_loose(value: str) -> str:
    cleaned = ensure_ascii_text(value).lower()
    cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def simplify_title(value: str) -> str:
    base = normalize_loose(value)
    tokens = [token for token in base.split() if token not in QUALIFIER_WORDS and not token.isdigit()]
    return " ".join(tokens).strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(a=normalize(a), b=normalize(b)).ratio()


def list_audio_files(folder: Path) -> list[Path]:
    return sorted(path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def sanitize_artist_name(value: str) -> str:
    cleaned = ensure_ascii_text(value).strip()
    cleaned = re.sub(r"[+_]+$", "", cleaned).strip()
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned or "Artista"


def folder_sort_key(root: Path, folder: Path) -> str:
    try:
        relative = folder.relative_to(root)
        return normalize(str(relative))
    except ValueError:
        return normalize(str(folder))


def discover_artist_folders(root: Path) -> list[Path]:
    found: list[Path] = []
    for current_root, dirnames, filenames in os.walk(root):
        current_path = Path(current_root)
        if current_path.name == STATE_DIRNAME:
            dirnames[:] = []
            continue
        dirnames[:] = [name for name in dirnames if not name.startswith(".")]
        audio_names = [name for name in filenames if Path(name).suffix.lower() in AUDIO_EXTENSIONS]
        is_scan_root = current_path.resolve() == root.resolve()
        if audio_names and (not is_scan_root or not dirnames):
            found.append(current_path)
            dirnames[:] = []
    return sorted(found, key=lambda item: folder_sort_key(root, item))


@dataclass
class LocalTrack:
    file_name: str
    title: str
    track_number: int | None = None


@dataclass
class LocalAlbum:
    name: str
    track_count: int
    track_numbers: list[int] = field(default_factory=list)
    tracks: list[LocalTrack] = field(default_factory=list)

    @property
    def missing_numbers(self) -> list[int]:
        if not self.track_numbers:
            return []
        sorted_numbers = sorted({number for number in self.track_numbers if number > 0})
        if not sorted_numbers:
            return []
        expected = set(range(sorted_numbers[0], sorted_numbers[-1] + 1))
        return sorted(expected - set(sorted_numbers))


@dataclass
class PublicRelease:
    name: str
    track_count: int
    kind: str
    url: str | None = None


@dataclass
class AlbumAssessment:
    status: str
    local_name: str
    public_name: str | None
    note: str
    local_track_count: int
    public_track_count: int | None
    score: float
    public_url: str | None = None


class AppContext:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.state_dir = self.root / STATE_DIRNAME
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.state_dir / STATE_FILENAME
        self.control_path = self.state_dir / CONTROL_FILENAME
        self.log_path = self.state_dir / LOG_FILENAME
        self.progress_path = self.root / PROGRESS_FILENAME

    def log(self, message: str) -> None:
        line = f"[{utc_now()}] {message}\n"
        self.log_path.touch(exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(line)

    def load_state(self) -> dict[str, Any]:
        return read_json(self.state_path, {})

    def save_state(self, payload: dict[str, Any]) -> None:
        write_json(self.state_path, payload)

    def load_control(self) -> dict[str, Any]:
        return read_json(self.control_path, {})

    def save_control(self, payload: dict[str, Any]) -> None:
        write_json(self.control_path, payload)


def split_base_name(base_name: str) -> list[str]:
    return [part.strip() for part in base_name.split(" - ") if part.strip()]


def infer_track(parts: list[str]) -> tuple[str, str | None, int | None]:
    if len(parts) >= 4 and re.fullmatch(r"\d{1,2}", parts[2]):
        return parts[0], parts[1], int(parts[2])
    if len(parts) >= 3 and re.fullmatch(r"\d{1,2}", parts[1]):
        return "", "Faixas avulsas", int(parts[1])
    return "", None, None


def parse_local_albums(folder: Path) -> tuple[str, list[LocalAlbum], int]:
    files = list_audio_files(folder)
    artist_name = sanitize_artist_name(folder.name)
    album_map: dict[str, list[LocalTrack]] = {}

    for file_path in files:
        base_name = file_path.stem
        parts = split_base_name(base_name)
        parsed_artist, parsed_album, track_number = infer_track(parts)
        if parsed_artist:
            artist_name = sanitize_artist_name(parsed_artist)
        if parsed_album:
            title = parts[-1] if parts else base_name
            album_map.setdefault(parsed_album, []).append(
                LocalTrack(file_name=file_path.name, title=ensure_ascii_text(title), track_number=track_number)
            )
            continue
        album_map.setdefault("Faixas avulsas", []).append(
            LocalTrack(file_name=file_path.name, title=ensure_ascii_text(base_name), track_number=None)
        )

    albums: list[LocalAlbum] = []
    for name, tracks in album_map.items():
        track_numbers = [track.track_number for track in tracks if track.track_number is not None]
        albums.append(
            LocalAlbum(
                name=ensure_ascii_text(name),
                track_count=len(tracks),
                track_numbers=sorted(track_numbers),
                tracks=sorted(tracks, key=lambda track: (track.track_number is None, track.track_number or 0, normalize(track.title))),
            )
        )

    albums.sort(key=lambda album: normalize(album.name))
    return artist_name, albums, len(files)


def fetch_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    query = urlencode(params)
    request = Request(f"{url}?{query}", headers={"User-Agent": "Discografia/1.0"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_apple_music_catalog(artist_name: str) -> tuple[list[PublicRelease], list[str]]:
    notes: list[str] = []
    releases: list[PublicRelease] = []
    safe_artist = ensure_ascii_text(artist_name)
    try:
        search = fetch_json(
            "https://itunes.apple.com/search",
            {
                "term": safe_artist,
                "media": "music",
                "entity": "musicArtist",
                "attribute": "artistTerm",
                "limit": 10,
                "country": "BR",
            },
        )
    except (HTTPError, URLError) as exc:
        notes.append(
            f"consulta ao Apple Music indisponivel neste passo ({type(exc).__name__}); comparacao mantida no nivel mais seguro pelo acervo da pasta"
        )
        return releases, notes

    candidates = search.get("results", [])
    if not candidates:
        return releases, [f"nenhuma referencia publica confiavel localizada no Apple Music em {format_date_for_md()} para `{safe_artist}`"]

    best_artist = max(candidates, key=lambda item: similarity(safe_artist, item.get("artistName", "")))
    best_score = similarity(safe_artist, best_artist.get("artistName", ""))
    if best_score < 0.62:
        notes.append("referencia publica de Apple Music nao registrada com seguranca neste passo; comparacao mantida no nivel mais seguro pelo acervo da pasta")
        return releases, notes

    try:
        lookup = fetch_json(
            "https://itunes.apple.com/lookup",
            {
                "id": best_artist["artistId"],
                "entity": "album",
                "limit": 200,
                "country": "BR",
            },
        )
    except (HTTPError, URLError) as exc:
        notes.append(
            f"catalogo do Apple Music indisponivel neste passo ({type(exc).__name__}); comparacao mantida no nivel mais seguro pelo acervo da pasta"
        )
        return releases, notes

    seen: set[str] = set()
    for item in lookup.get("results", [])[1:]:
        collection_name = item.get("collectionName")
        if not collection_name:
            continue
        key = normalize(collection_name)
        if not key or key in seen:
            continue
        seen.add(key)
        releases.append(
            PublicRelease(
                name=ensure_ascii_text(collection_name),
                track_count=int(item.get("trackCount") or 0),
                kind=ensure_ascii_text(item.get("collectionType") or "album"),
                url=item.get("collectionViewUrl"),
            )
        )

    releases.sort(key=lambda release: normalize(release.name))
    notes.append(
        f"Apple Music: artista `{ensure_ascii_text(best_artist.get('artistName', artist_name))}`, com {len(releases)} lancamentos visiveis em {format_date_for_md()}"
    )
    return releases, notes


def release_flags(value: str) -> set[str]:
    normalized = normalize_loose(value)
    flags: set[str] = set()
    if "playback" in normalized:
        flags.add("playback")
    if "karaoke" in normalized:
        flags.add("karaoke")
    if "instrumental" in normalized:
        flags.add("instrumental")
    if "ao vivo" in normalize(value) or " live " in f" {normalized} ":
        flags.add("live")
    if "acustico" in normalized:
        flags.add("acustico")
    return flags


def compare_album_titles(local_name: str, public_name: str) -> tuple[float, str]:
    exact_score = similarity(local_name, public_name)
    local_simple = simplify_title(local_name)
    public_simple = simplify_title(public_name)
    simple_score = SequenceMatcher(a=local_simple, b=public_simple).ratio() if local_simple and public_simple else 0.0
    local_flags = release_flags(local_name)
    public_flags = release_flags(public_name)
    mismatch = local_flags.symmetric_difference(public_flags)
    score = max(exact_score, simple_score)
    if "playback" in mismatch:
        score -= 0.24
    if "karaoke" in mismatch or "instrumental" in mismatch:
        score -= 0.16
    if "live" in mismatch:
        score -= 0.08
    if "acustico" in mismatch:
        score -= 0.05
    score = max(0.0, min(score, 1.0))
    if exact_score >= 0.96:
        return score, "titulo_equivalente"
    if local_simple and local_simple == public_simple:
        return score, "mesmo_nucleo_com_edicao_diferente"
    if exact_score >= 0.82 or simple_score >= 0.86:
        return score, "similaridade_forte"
    return score, "similaridade_fraca"


def should_report_missing_release(release: PublicRelease, local_albums: list[LocalAlbum]) -> bool:
    release_flag_set = release_flags(release.name)
    if {"playback", "karaoke", "instrumental"} & release_flag_set:
        return any(release_flag_set & release_flags(album.name) for album in local_albums)
    return True


def assess_catalog(local_albums: list[LocalAlbum], public_releases: list[PublicRelease]) -> tuple[list[AlbumAssessment], list[PublicRelease], list[str]]:
    unmatched_public = list(public_releases)
    assessments: list[AlbumAssessment] = []
    notes: list[str] = []

    for album in local_albums:
        if album.name == "Faixas avulsas" and not public_releases:
            assessments.append(
                AlbumAssessment(
                    status="partial",
                    local_name=album.name,
                    public_name=None,
                    note="a pasta tem faixas avulsas sem catalogo publico disponivel para confronto seguro",
                    local_track_count=album.track_count,
                    public_track_count=None,
                    score=0.0,
                )
            )
            continue

        ranked: list[tuple[float, str, PublicRelease]] = []
        for release in unmatched_public:
            release_flag_set = release_flags(release.name)
            album_flag_set = release_flags(album.name)
            if "playback" in release_flag_set and "playback" not in album_flag_set:
                continue
            if {"karaoke", "instrumental"} & release_flag_set and not ({"karaoke", "instrumental"} & album_flag_set):
                continue
            score, reason = compare_album_titles(album.name, release.name)
            if score >= 0.74:
                ranked.append((score, reason, release))
        ranked.sort(key=lambda item: (item[0], item[2].track_count), reverse=True)
        best = ranked[0] if ranked else None

        if not best:
            note = "album local claro, sem correspondencia publica confiavel suficiente"
            if album.missing_numbers:
                note += f"; numeracao local com lacunas {album.missing_numbers}"
            assessments.append(
                AlbumAssessment(
                    status="partial",
                    local_name=album.name,
                    public_name=None,
                    note=note,
                    local_track_count=album.track_count,
                    public_track_count=None,
                    score=0.0,
                )
            )
            continue

        score, reason, release = best
        unmatched_public.remove(release)
        same_count = bool(album.track_count and release.track_count and album.track_count == release.track_count)

        if same_count and score >= 0.90 and reason in {"titulo_equivalente", "similaridade_forte"}:
            assessments.append(
                AlbumAssessment(
                    status="present",
                    local_name=album.name,
                    public_name=release.name,
                    note="quantidade de faixas alinhada com o catalogo publico",
                    local_track_count=album.track_count,
                    public_track_count=release.track_count,
                    score=score,
                    public_url=release.url,
                )
            )
            continue

        note_bits = []
        if reason == "mesmo_nucleo_com_edicao_diferente":
            note_bits.append("mesmo nucleo de titulo, mas com indicio de edicao diferente")
        elif reason == "similaridade_forte":
            note_bits.append("titulo bastante proximo ao lancamento publico")
        else:
            note_bits.append("correspondencia parcial, mantida em modo conservador")
        if release.track_count:
            note_bits.append(f"pasta local com {album.track_count} faixa(s) versus {release.track_count} no Apple Music")
        if album.missing_numbers:
            note_bits.append(f"lacunas de numeracao local: {album.missing_numbers}")
        assessments.append(
            AlbumAssessment(
                status="partial",
                local_name=album.name,
                public_name=release.name,
                note="; ".join(note_bits),
                local_track_count=album.track_count,
                public_track_count=release.track_count,
                score=score,
                public_url=release.url,
            )
        )

    missing = [release for release in unmatched_public if should_report_missing_release(release, local_albums)]
    if any(not should_report_missing_release(release, local_albums) for release in unmatched_public):
        notes.append("lancamentos marcados como playback, karaoke ou instrumental foram retirados da lista principal de ausencias")
    return assessments, missing, notes


def render_inventory(local_albums: list[LocalAlbum]) -> list[str]:
    lines: list[str] = ["## Inventario local", ""]
    for album in local_albums:
        descriptor = f"`{ensure_ascii_text(album.name)}` - {album.track_count} faixa(s)"
        if album.track_numbers:
            descriptor += f"; numeros {album.track_numbers}"
        if album.missing_numbers:
            descriptor += f"; lacunas {album.missing_numbers}"
        lines.append(f"- {descriptor}")
    lines.append("")
    return lines


def build_markdown(artist_name: str, folder: Path, local_albums: list[LocalAlbum], public_releases: list[PublicRelease], public_notes: list[str]) -> str:
    safe_artist = ensure_ascii_text(artist_name)
    folder_text = ensure_ascii_text(str(folder))
    date_text = format_date_for_md()
    lines: list[str] = [
        f"# {safe_artist} - musicas faltantes",
        "",
        f"Comparacao feita em {date_text} entre:",
        "",
        f"- arquivos encontrados em `{folder_text}`",
        f"- catalogo publico encontrado em Apple Music para `{safe_artist}`",
        "",
        "## Resumo",
        "",
    ]

    if public_releases:
        assessments, missing_releases, assessment_notes = assess_catalog(local_albums, public_releases)
        present = [item for item in assessments if item.status == "present"]
        partial = [item for item in assessments if item.status == "partial"]
        lines.extend(
            [
                f"- arquivos locais avaliados: `{sum(album.track_count for album in local_albums)}`",
                f"- grupos locais identificados: `{len(local_albums)}`",
                f"- lancamentos publicos avaliados: `{len(public_releases)}`",
                f"- albums aparentemente presentes: `{len(present)}`",
                f"- albums com divergencia: `{len(partial)}`",
                f"- lancamentos ausentes da pasta: `{len(missing_releases)}`",
                "",
            ]
        )
        if local_albums:
            lines.extend(render_inventory(local_albums))
        if present:
            lines.extend(["## Albums que parecem presentes na pasta", ""])
            for item in present:
                lines.append(
                    f"- `{ensure_ascii_text(item.local_name)}` alinhado com `{ensure_ascii_text(item.public_name or '')}` ({item.local_track_count} faixa(s))"
                )
            lines.append("")
        if partial:
            lines.extend(["## Faltantes parciais ou com divergencia", ""])
            for item in partial:
                if item.public_name:
                    lines.append(
                        f"- `{ensure_ascii_text(item.local_name)}` versus `{ensure_ascii_text(item.public_name)}` - {ensure_ascii_text(item.note)}"
                    )
                else:
                    lines.append(f"- `{ensure_ascii_text(item.local_name)}` - {ensure_ascii_text(item.note)}")
            lines.append("")
        if missing_releases:
            lines.extend(["## Lancamentos ausentes da pasta", ""])
            for release in missing_releases[:60]:
                lines.append(f"- `{ensure_ascii_text(release.name)}` - {release.track_count} faixa(s)")
            lines.append("")
        lines.extend(["## Observacao", ""])
        if present or partial:
            lines.append("Mantive a comparacao no nivel conservador, privilegiando titulo, edicao e contagem de faixas antes de assumir equivalencia total.")
        else:
            lines.append("Mantive a comparacao no nivel mais seguro porque nao houve correspondencia suficiente entre a organizacao local e o catalogo publico.")
        lines.extend(["", "## Fontes", ""])
        for note in assessment_notes:
            lines.append(f"- {ensure_ascii_text(note)}")
        for note in public_notes:
            lines.append(f"- {ensure_ascii_text(note)}")
        for release in public_releases[:20]:
            if release.url:
                lines.append(f"- Apple Music: `{ensure_ascii_text(release.name)}` - {release.url}")
    else:
        lines.extend(
            [
                "- arquivos locais avaliados: `0`" if not local_albums else f"- arquivos locais avaliados: `{sum(album.track_count for album in local_albums)}`",
                f"- grupos locais identificados: `{len(local_albums)}`",
                "- lancamentos publicos avaliados: `0`",
                "",
            ]
        )
        if local_albums:
            lines.extend(render_inventory(local_albums))
        lines.extend(
            [
                "## Observacao",
                "",
                "Mantive a comparacao no nivel mais seguro, baseada no acervo local claramente organizado.",
                "",
                "## Fontes",
                "",
            ]
        )
        for note in public_notes:
            lines.append(f"- {ensure_ascii_text(note)}")

    return "\n".join(lines).strip() + "\n"


def choose_batch_size(total_remaining: int) -> int:
    cpu_count = os.cpu_count() or 2
    if total_remaining <= 2:
        return total_remaining
    if cpu_count <= 2:
        return 2
    if cpu_count <= 4:
        return min(3, total_remaining)
    return min(4, total_remaining)


def refresh_queue(root: Path) -> list[dict[str, str]]:
    return [{"folder": str(folder), "artist_hint": sanitize_artist_name(folder.name)} for folder in discover_artist_folders(root)]


def output_filename(artist_name: str) -> str:
    return f"{ascii_slug(artist_name)}_musicas_faltantes.md"


def update_state_after_artist(state: dict[str, Any], artist_name: str, output_file: str, next_artist: str, next_folder: str) -> dict[str, Any]:
    recent = state.get("recent_completed", [])
    if output_file in recent:
        recent.remove(output_file)
    recent.insert(0, output_file)
    state.update(
        {
            "last_artist": artist_name,
            "last_output_file": output_file,
            "next_artist": next_artist,
            "next_folder": next_folder,
            "recent_completed": recent[:200],
            "updated_at": utc_now(),
        }
    )
    return state


def load_or_create_state(ctx: AppContext, root: Path) -> dict[str, Any]:
    existing = ctx.load_state()
    queue = refresh_queue(root)
    defaults = {
        "root": str(root),
        "queue": queue,
        "index": 0,
        "status": "idle",
        "current_artist": None,
        "last_artist": "nenhum",
        "last_output_file": "nenhum",
        "next_artist": queue[0]["artist_hint"] if queue else "fim da fila atual",
        "next_folder": queue[0]["folder"] if queue else "nenhuma",
        "recent_completed": [],
        "updated_at": utc_now(),
        "batch_size": choose_batch_size(len(queue)),
        "errors": [],
    }
    if not existing or existing.get("root") != str(root):
        return defaults

    existing["queue"] = queue
    if existing.get("last_output_file") not in {"nenhum", None}:
        last_output = existing["last_output_file"]
        resolved_index = 0
        for idx, item in enumerate(queue):
            if output_filename(item["artist_hint"]) == last_output:
                resolved_index = idx + 1
        existing["index"] = min(resolved_index, len(queue))
    existing["batch_size"] = choose_batch_size(max(len(queue) - int(existing.get("index", 0)), 0))
    existing["next_artist"] = queue[existing["index"]]["artist_hint"] if existing["index"] < len(queue) else "fim da fila atual"
    existing["next_folder"] = queue[existing["index"]]["folder"] if existing["index"] < len(queue) else "nenhuma"
    existing["updated_at"] = utc_now()
    return existing


def write_progress(ctx: AppContext, state: dict[str, Any]) -> None:
    recent = state.get("recent_completed", [])
    current_file = state.get("last_output_file", "nenhum")
    current_artist = state.get("last_artist", "nenhum")
    next_artist = state.get("next_artist", "fim da fila atual")
    next_folder = state.get("next_folder", "nenhuma")
    status = state.get("status", "desconhecido")
    lines = [
        "# Progresso Musicas Faltantes",
        "",
        f"Ultima atualizacao: {format_date_for_md()}",
        "",
        "## Estado atual",
        "",
        f"- status_execucao: `{status}`",
        f"- ultimo_arquivo_concluido: `{current_file}`",
        f"- ultimo_artista_concluido: `{ensure_ascii_text(current_artist)}`",
        f"- proximo_artista_sugerido: `{ensure_ascii_text(next_artist)}`",
        f"- pasta_local_do_proximo: `{ensure_ascii_text(next_folder)}`",
        f"- criterio_de_ordem: nome da pasta em `{ensure_ascii_text(str(ctx.root))}`, seguindo sequencia alfabetica pratica do lote",
        "",
        "## Ultimos concluidos",
        "",
    ]
    if recent:
        lines.extend(f"- `{ensure_ascii_text(item)}`" for item in recent[:200])
    else:
        lines.append("- nenhum arquivo concluido ainda")
    lines.extend(
        [
            "",
            "## Regra de retomada",
            "",
            "- antes de continuar, ler este arquivo e abrir o ultimo `.md` concluido",
            f"- confirmar o proximo artista pela ordem alfabetica das pastas em `{ensure_ascii_text(str(ctx.root))}`",
            "- ao finalizar cada artista, atualizar imediatamente `ultimo_arquivo_concluido`, `ultimo_artista_concluido`, `proximo_artista_sugerido` e a lista de `Ultimos concluidos`",
            "- se houver travamento, usar este arquivo como fonte primaria de continuidade, sem depender de memoria conversacional",
            "",
        ]
    )
    ctx.progress_path.write_text("\n".join(lines), encoding="utf-8")


def handle_control(ctx: AppContext, state: dict[str, Any]) -> str | None:
    control = ctx.load_control()
    action = control.get("action")
    if action == "cancel":
        state["status"] = "cancelado"
        state["updated_at"] = utc_now()
        ctx.save_state(state)
        ctx.log("Execucao cancelada por comando externo.")
        return "cancel"
    if action == "pause":
        state["status"] = "pausado"
        state["updated_at"] = utc_now()
        ctx.save_state(state)
        ctx.log("Execucao pausada por comando externo.")
        return "pause"
    return None


def process_run(root: Path, resume: bool) -> int:
    ctx = AppContext(root)
    state = load_or_create_state(ctx, root)
    if not resume:
        state = load_or_create_state(ctx, root)
        state["index"] = 0
        state["queue"] = refresh_queue(root)
        state["batch_size"] = choose_batch_size(len(state["queue"]))
        state["next_artist"] = state["queue"][0]["artist_hint"] if state["queue"] else "fim da fila atual"
        state["next_folder"] = state["queue"][0]["folder"] if state["queue"] else "nenhuma"
        state["current_artist"] = None
        state["updated_at"] = utc_now()
    elif state.get("status") == "concluido":
        state["index"] = 0
        state["queue"] = refresh_queue(root)
        state["batch_size"] = choose_batch_size(len(state["queue"]))
        state["next_artist"] = state["queue"][0]["artist_hint"] if state["queue"] else "fim da fila atual"
        state["next_folder"] = state["queue"][0]["folder"] if state["queue"] else "nenhuma"

    state["status"] = "rodando"
    state["updated_at"] = utc_now()
    ctx.save_state(state)
    ctx.save_control({})
    write_progress(ctx, state)
    ctx.log(f"Execucao iniciada em {root}")

    queue = state["queue"]
    while state["index"] < len(queue):
        command = handle_control(ctx, state)
        if command == "cancel":
            print("Execucao cancelada.")
            return 2
        if command == "pause":
            print("Execucao pausada.")
            return 3

        remaining = len(queue) - state["index"]
        state["batch_size"] = choose_batch_size(remaining)
        current = queue[state["index"]]
        folder = Path(current["folder"])
        state["current_artist"] = current["artist_hint"]
        state["updated_at"] = utc_now()
        ctx.save_state(state)

        try:
            artist_name, local_albums, _ = parse_local_albums(folder)
            public_releases, public_notes = fetch_apple_music_catalog(artist_name)
            markdown = build_markdown(artist_name, folder, local_albums, public_releases, public_notes)
            output_file = output_filename(artist_name)
            (root / output_file).write_text(markdown, encoding="utf-8")
            state["index"] += 1
            next_artist = queue[state["index"]]["artist_hint"] if state["index"] < len(queue) else "fim da fila atual"
            next_folder = queue[state["index"]]["folder"] if state["index"] < len(queue) else "nenhuma"
            state = update_state_after_artist(state, artist_name, output_file, next_artist, next_folder)
            state["status"] = "rodando"
            ctx.save_state(state)
            write_progress(ctx, state)
            ctx.log(f"Concluido: {artist_name}")
            print(f"[{state['index']}/{len(queue)}] {artist_name}")
        except Exception as exc:  # noqa: BLE001
            message = f"{type(exc).__name__}: {exc}"
            errors = state.get("errors", [])
            errors.append({"artist": current["artist_hint"], "error": message, "at": utc_now()})
            state["errors"] = errors[-100:]
            state["status"] = "erro"
            state["updated_at"] = utc_now()
            ctx.save_state(state)
            write_progress(ctx, state)
            ctx.log(f"Erro em {current['artist_hint']}: {message}")
            print(f"Erro em {current['artist_hint']}: {message}", file=sys.stderr)
            return 1

        time.sleep(0.2)

    state["status"] = "concluido"
    state["current_artist"] = None
    state["next_artist"] = "fim da fila atual"
    state["next_folder"] = "nenhuma"
    state["updated_at"] = utc_now()
    ctx.save_state(state)
    write_progress(ctx, state)
    ctx.log("Fila concluida.")
    print("Fila concluida.")
    return 0


def process_signal(root: Path, action: str) -> int:
    ctx = AppContext(root)
    ctx.save_control({"action": action, "updated_at": utc_now()})
    ctx.log(f"Sinal gravado: {action}")
    print(f"Sinal registrado: {action}")
    return 0


def process_status(root: Path) -> int:
    ctx = AppContext(root)
    state = ctx.load_state()
    if not state:
        print("Nenhum estado encontrado.")
        return 0
    print(json.dumps(state, ensure_ascii=True, indent=2))
    return 0

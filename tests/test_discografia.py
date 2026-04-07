from __future__ import annotations

import shutil
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from discografia.core import (
    PublicRelease,
    assess_catalog,
    parse_local_albums,
    process_run,
)


class DiscografiaTests(unittest.TestCase):
    def test_parse_local_albums_sanitizes_artist_and_tracks(self) -> None:
        with workspace_tempdir() as tmp:
            folder = Path(tmp) / "Ze Marco e Adriano++"
            folder.mkdir()
            (folder / "Ze Marco e Adriano - Sonho - 01 - De Bem com a Vida.mp3").write_text("", encoding="utf-8")
            (folder / "Ze Marco e Adriano - Sonho - 03 - Outra.mp3").write_text("", encoding="utf-8")

            artist, albums, total = parse_local_albums(folder)

            self.assertEqual(artist, "Ze Marco e Adriano")
            self.assertEqual(total, 2)
            self.assertEqual(len(albums), 1)
            self.assertEqual(albums[0].name, "Sonho")
            self.assertEqual(albums[0].missing_numbers, [2])

    def test_assess_catalog_ignores_playback_as_main_missing_signal(self) -> None:
        releases = [
            PublicRelease(name="Sonho", track_count=2, kind="album"),
            PublicRelease(name="Sonho (Playback)", track_count=2, kind="album"),
            PublicRelease(name="Encontro", track_count=10, kind="album"),
        ]
        local_albums = parse_local_albums_from_names(
            [
                "Ze Marco e Adriano - Sonho - 01 - A.mp3",
                "Ze Marco e Adriano - Sonho - 02 - B.mp3",
            ]
        )

        assessments, missing, notes = assess_catalog(local_albums, releases)

        self.assertEqual([item.status for item in assessments], ["present"])
        self.assertEqual([item.name for item in missing], ["Encontro"])
        self.assertTrue(any("playback" in note for note in notes))

    def test_process_run_generates_report_and_progress(self) -> None:
        with workspace_tempdir() as tmp:
            root = Path(tmp)
            folder = root / "Artista Exemplo"
            folder.mkdir()
            (folder / "Artista Exemplo - Album Um - 01 - Faixa A.mp3").write_text("", encoding="utf-8")
            (folder / "Artista Exemplo - Album Um - 02 - Faixa B.mp3").write_text("", encoding="utf-8")

            releases = [PublicRelease(name="Album Um", track_count=2, kind="album", url="https://example.test/album-um")]
            with patch("discografia.core.fetch_apple_music_catalog", return_value=(releases, ["catalogo simulado"])):
                exit_code = process_run(root, resume=False)

            self.assertEqual(exit_code, 0)
            report = (root / "artista_exemplo_musicas_faltantes.md").read_text(encoding="utf-8")
            progress = (root / "PROGRESSO_MUSICAS_FALTANTES.md").read_text(encoding="utf-8")
            self.assertIn("## Inventario local", report)
            self.assertIn("albums aparentemente presentes", report)
            self.assertIn("status_execucao", progress)


def parse_local_albums_from_names(file_names: list[str]):
    with workspace_tempdir() as tmp:
        folder = Path(tmp) / "tmp"
        folder.mkdir()
        for file_name in file_names:
            (folder / file_name).write_text("", encoding="utf-8")
        _, albums, _ = parse_local_albums(folder)
        return albums


@contextmanager
def workspace_tempdir():
    root = Path(__file__).resolve().parent.parent / f"_tmp_test_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    try:
        yield str(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

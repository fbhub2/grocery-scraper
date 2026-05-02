import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import db
import tasks


class TestRunAutoNormalize:
    def test_oppdaterer_auto_name(self, tmp_db):
        db.upsert_normal("lettmelk")
        tasks.run_auto_normalize()
        row = next(r for r in db.list_normals() if r["original_name"] == "lettmelk")
        assert row["auto_name"] == "lett melk"

    def test_hopper_over_eksisterende(self, tmp_db):
        db.upsert_normal("lettmelk", auto_name="eksisterende")
        tasks.run_auto_normalize()
        row = next(r for r in db.list_normals() if r["original_name"] == "lettmelk")
        assert row["auto_name"] == "eksisterende"

    def test_returnerer_antall(self, tmp_db):
        db.upsert_normal("lettmelk")
        db.upsert_normal("helmelk")
        db.upsert_normal("smør", auto_name="allerede satt")
        count = tasks.run_auto_normalize()
        assert count == 2

    def test_tom_tabell(self, tmp_db):
        assert tasks.run_auto_normalize() == 0

    def test_normaliserer_flere(self, tmp_db):
        db.upsert_normal("havregryn")
        db.upsert_normal("knekkebrød")
        tasks.run_auto_normalize()
        normals = {r["original_name"]: r["auto_name"] for r in db.list_normals()}
        assert normals["havregryn"] == "havre gryn"
        assert normals["knekkebrød"] == "knekke brød"

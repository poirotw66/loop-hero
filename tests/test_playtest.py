"""Smoke test that an automated playtest meta-run completes."""

from scripts.playtest import simulate_meta


def test_playtest_meta_completes_with_progress() -> None:
    meta = simulate_meta(num_runs=8, seed_base=7)
    assert len(meta["runs"]) == 8
    assert meta["avg_loops"] > 0
    assert meta["stranded_grid_enemy_runs"] == 0
    # At least some expeditions should fill the boss meter.
    assert any(report.boss_spawned for report in meta["runs"])

from pathlib import Path

from core.panel_store import PanelStore
from models.panel import Panel


def test_save_and_get_page(tmp_path: Path):
    store = PanelStore(tmp_path)
    saved = store.save_from_panels(1, 1000, 2000, [Panel(order=1, x=0, y=0, width=200, height=300)])
    loaded = store.get_page(1)
    assert loaded is not None
    assert loaded.page == 1
    assert loaded.panels[0].id == saved.panels[0].id

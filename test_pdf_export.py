import importlib.util
import os
import shutil
import tempfile


def _load_dloto_module():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "D-Loto.py")
    spec = importlib.util.spec_from_file_location("dloto_module_under_test_pdf", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dloto = _load_dloto_module()


class _FakeTreeview:
    """Duck-typed stand-in for ttk.Treeview — capture_table_to_pdf only
    calls cget('columns'), get_children(), item(child, 'values'), and
    column(col, 'width')."""
    def __init__(self, columns, rows, col_widths):
        self._columns = columns
        self._rows = rows
        self._col_widths = dict(zip(columns, col_widths))

    def cget(self, key):
        assert key == "columns"
        return self._columns

    def get_children(self):
        return list(range(len(self._rows)))

    def item(self, child, key):
        assert key == "values"
        return self._rows[child]

    def column(self, col, key):
        assert key == "width"
        return self._col_widths[col]


def test_capture_table_to_pdf_handles_special_characters_and_long_text():
    tmp_dir = tempfile.mkdtemp(prefix="dloto_pdf_test_")
    try:
        columns = ("LOTO No.", "Work Description", "Status")
        col_widths = [90, 440, 95]
        long_title = "Isolate Valve A & B <manual override> for overhaul " * 5
        rows = [("1", long_title, "Active")]
        fake = _FakeTreeview(columns, rows, col_widths)

        out_path = os.path.join(tmp_dir, "test.pdf")
        dloto.capture_table_to_pdf(fake, out_path)

        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 0
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_capture_table_to_pdf_handles_empty_table():
    tmp_dir = tempfile.mkdtemp(prefix="dloto_pdf_test_")
    try:
        columns = ("LOTO No.", "Work Description", "Status")
        col_widths = [90, 440, 95]
        fake = _FakeTreeview(columns, [], col_widths)

        out_path = os.path.join(tmp_dir, "empty.pdf")
        dloto.capture_table_to_pdf(fake, out_path)

        assert os.path.exists(out_path)
        assert os.path.getsize(out_path) > 0
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_capture_table_to_pdf_handles_special_characters_and_long_text()
    test_capture_table_to_pdf_handles_empty_table()
    print("All tests passed.")

import pytest

from app.documents import chunk_text, extract_text


def test_chunks_overlap_and_cover_the_text():
    text = "".join(str(i % 10) for i in range(250))
    chunks = chunk_text(text, size=100, overlap=10)

    assert [len(chunk) for chunk in chunks] == [100, 100, 70]
    assert chunks[0][-10:] == chunks[1][:10]
    assert chunks[-1].endswith(text[-10:])


def test_whitespace_is_collapsed():
    assert chunk_text("a \n\n b\tc", size=10, overlap=0) == ["a b c"]


def test_empty_text_gives_no_chunks():
    assert chunk_text("   ", size=10, overlap=0) == []


@pytest.mark.parametrize("size, overlap", [(0, 0), (10, 10), (10, -1)])
def test_invalid_chunk_settings_are_rejected(size, overlap):
    with pytest.raises(ValueError):
        chunk_text("text", size=size, overlap=overlap)


def test_text_files_are_decoded():
    assert extract_text("notes.MD", "héllo".encode()) == "héllo"


def test_unsupported_files_are_rejected():
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_text("image.png", b"data")

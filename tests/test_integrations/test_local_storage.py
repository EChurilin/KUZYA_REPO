import pytest
from pathlib import Path
from src.integrations.storage.local_storage import LocalScreenshotStorage

def test_save_and_delete_file(tmp_path):
    storage_dir = tmp_path / "storage" / "screenshots"
    storage = LocalScreenshotStorage(str(storage_dir))
    
    file_bytes = b"fake image data"
    relative_path = storage.save_file(file_bytes, "jpg")
    
    assert relative_path.startswith("storage/screenshots/")
    assert relative_path.endswith(".jpg")
    
    full_path = tmp_path / relative_path
    assert full_path.exists()
    assert full_path.read_bytes() == file_bytes
    
    result = storage.delete_file(relative_path)
    assert result is True
    assert not full_path.exists()

def test_delete_non_existent_file(tmp_path):
    storage_dir = tmp_path / "storage" / "screenshots"
    storage = LocalScreenshotStorage(str(storage_dir))
    
    result = storage.delete_file("storage/screenshots/non_existent.jpg")
    assert result is False

def test_path_traversal_prevention(tmp_path):
    storage_dir = tmp_path / "storage" / "screenshots"
    storage = LocalScreenshotStorage(str(storage_dir))
    
    # Создаем файл вне директории хранилища
    outside_file = tmp_path / "secret.txt"
    outside_file.write_text("secret")
    
    # Пытаемся удалить его через path traversal
    result = storage.delete_file("storage/screenshots/../../secret.txt")
    
    # Должно вернуть False, а файл остаться нетронутым
    assert result is False
    assert outside_file.exists()
    assert outside_file.read_text() == "secret"

def test_unsupported_extension_fallback(tmp_path):
    storage_dir = tmp_path / "storage" / "screenshots"
    storage = LocalScreenshotStorage(str(storage_dir))
    
    relative_path = storage.save_file(b"data", "exe")
    assert relative_path.endswith(".jpg")
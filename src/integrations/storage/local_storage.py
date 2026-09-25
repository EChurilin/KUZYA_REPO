import uuid
from pathlib import Path

class LocalScreenshotStorage:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path).resolve()
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_bytes: bytes, extension: str) -> str:
        self._ensure_dir()
        ext = extension.lstrip('.').lower()
        if ext not in ('jpg', 'jpeg', 'png', 'webp'):
            ext = 'jpg'  # fallback для безопасности
            
        filename = f"{uuid.uuid4().hex}.{ext}"
        file_path = self.base_path / filename
        
        with open(file_path, "wb") as f:
            f.write(file_bytes)
            
        # Возвращаем относительный путь для сохранения в БД
        return f"storage/screenshots/{filename}"

    def delete_file(self, relative_path: str) -> bool:
        try:
            # Извлекаем только имя файла из относительного пути для максимальной безопасности
            filename = Path(relative_path).name
            file_path = (self.base_path / filename).resolve()
            
            # Проверка безопасности: путь должен находиться строго внутри base_path
            file_path.relative_to(self.base_path)
            
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                return True
        except (ValueError, OSError):
            # ValueError: попытка выхода за пределы директории (path traversal)
            # OSError: некорректный путь
            pass
            
        return False
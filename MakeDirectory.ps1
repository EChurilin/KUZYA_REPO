# Создаём корневую папку
New-Item -ItemType Directory -Path "telegram-reward-bot"
cd telegram-reward-bot

# Создаём структуру
$folders = @(
    "src\config",
    "src\core",
    "src\repositories",
    "src\services",
    "src\utils",
    "src\bots\client_bot\handlers",
    "src\bots\client_bot\middlewares",
    "src\bots\client_bot\keyboards",
    "src\bots\staff_bot\handlers",
    "src\bots\staff_bot\middlewares",
    "src\bots\staff_bot\keyboards",
    "src\integrations\telegram",
    "src\integrations\database\migrations",
    "src\integrations\cache",
    "tests\unit",
    "tests\integration",
    "tests\fixtures"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Path $folder -Force
}

# Создаём __init__.py файлы
$initFiles = @(
    "src\__init__.py",
    "src\config\__init__.py",
    "src\core\__init__.py",
    "src\repositories\__init__.py",
    "src\services\__init__.py",
    "src\utils\__init__.py",
    "src\bots\__init__.py",
    "src\bots\client_bot\__init__.py",
    "src\bots\client_bot\handlers\__init__.py",
    "src\bots\client_bot\middlewares\__init__.py",
    "src\bots\client_bot\keyboards\__init__.py",
    "src\bots\staff_bot\__init__.py",
    "src\bots\staff_bot\handlers\__init__.py",
    "src\bots\staff_bot\middlewares\__init__.py",
    "src\bots\staff_bot\keyboards\__init__.py",
    "src\integrations\__init__.py",
    "src\integrations\telegram\__init__.py",
    "src\integrations\database\__init__.py",
    "src\integrations\cache\__init__.py",
    "tests\__init__.py",
    "tests\unit\__init__.py",
    "tests\integration\__init__.py"
)

foreach ($file in $initFiles) {
    New-Item -ItemType File -Path $file -Force
}
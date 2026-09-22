#!/bin/bash
# Сборка документации mkdocs в папку public

set -e

echo "Сборка документации..."
python3 -m mkdocs build -d public

echo "Копирование scalar.html..."
cp docs/api/scalar.html public/api/scalar.html

echo "Готово! public/ собран."

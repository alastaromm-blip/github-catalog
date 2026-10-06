# GitHub Catalog — автообновляемая таблица лучших решений GitHub

1675 репозиториев для вайбкодеров в Google Таблице: категории, русские описания,
команды быстрого старта, звезды и активность.

## Структура
- `github_catalog_sync.py` — сбор сидов + обогащение по GitHub API
- `enrich_delta.py` — добавляет только новые репо
- `fetch_readme.py` — тянет README для богатых описаний
- `translate_long.py` — переписывает описания по-русски через LLM
- `improve_sheet.py` — заливка в Google Таблицу с дизайном (цвета хабов, зебра, фильтры)
- `fix_colors_order.py`, `fix_wrap.py` — финальный тюнинг вкладок

## Запуск вручную
```
export GITHUB_TOKEN=... OPENROUTER_KEY=...
python github_catalog_sync.py seeds --config config.json --out seeds.json
python enrich_delta.py && python fetch_readme.py && python translate_long.py
python swap_desc.py && python sort_stars.py
python improve_sheet.py --sheet SHEET_ID
```

## Автообновление
GitHub Actions: `.github/workflows/nightly-update.yml`, ежедневно 03:00 UTC.
Секреты: `GH_TOKEN`, `OPENROUTER_KEY`, `GSHEET_TOKEN_JSON` (OAuth-токен Google).

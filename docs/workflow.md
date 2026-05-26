# Workflow

End-to-end:

```
React/TS source
       |
       v
[ extractor ]  ->  extracted.json  (key, default_value, source_file, line, context)
       |
       v
[ orchestrator ]
   - translation memory lookup (skip if hit)
   - translator.translate(key, source, target_locale)
   - store as status=approved (or pending_review when a human is in the loop)
       |
       v
[ validators ]  (icu, plural, unicode, length)
       |
       v
[ writer ]  ->  locales/<lang>.json
```

## Locale targets

Default suite: `en` (source), `es`, `fr`, `de`, `ja`, `ar`, `zh-CN`, `hi`. Each was chosen to exercise a specific axis: Arabic is RTL with 6 plural categories, Japanese is single-category, Hindi exercises the multi-category path, French requires the `many` category.

## Translation memory

`InMemoryTM` is the default. `localebridge.store.TranslationRow` documents the production SQLAlchemy table shape; the schema is `(key, locale)` composite key, plus `source_text`, `translated_text`, `status`, `edit_reason`, `reject_reason`.

## Status lifecycle

```
pending_review --[approve]--> approved
              \-[edit]------> edited     (stores edit_reason; translator memory remembers)
              \-[reject]----> rejected   (stores reject_reason)
```

`edited` is final; the translator never overwrites an edited entry, which is how human edits become sticky across pipeline runs.

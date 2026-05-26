.PHONY: install lint typecheck test e2e bench bench-regress clean

install:
	pnpm install
	poetry -C apps/orchestrator install

lint:
	poetry -C apps/orchestrator run ruff check src tests

typecheck:
	pnpm -r --filter ./apps/extractor typecheck
	poetry -C apps/orchestrator run mypy src

test:
	pnpm -r --filter ./apps/extractor test
	poetry -C apps/orchestrator run pytest -q

e2e:
	pnpm --filter ./apps/extractor build
	node apps/extractor/dist/cli.js \
		--src examples/react-app/src \
		--out /tmp/localebridge-extracted.json
	poetry -C apps/orchestrator run localebridge-run \
		--input /tmp/localebridge-extracted.json \
		--locales examples/react-app/locales \
		--targets es,fr,de,ja,ar,zh-CN,hi

bench:
	poetry -C apps/orchestrator run python -m localebridge.bench --n 10000

bench-regress:
	poetry -C apps/orchestrator run python -m localebridge.bench --regress

clean:
	rm -rf node_modules apps/*/node_modules apps/*/dist
	rm -rf apps/orchestrator/.venv apps/orchestrator/.pytest_cache

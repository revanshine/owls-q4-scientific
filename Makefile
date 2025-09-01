# OWLS Q4 Scientific Pipeline - Reproducible Analysis
# One-liner commands to regenerate all results

.PHONY: help setup run plots test clean

help:  ## Show this help message
	@echo "OWLS Q4 Scientific Pipeline"
	@echo "=========================="
	@echo ""
	@echo "Quick Start:"
	@echo "  make setup    # Install dependencies"
	@echo "  make run      # Generate all results"
	@echo "  make plots    # Create visualizations"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

setup:  ## Install dependencies and prepare environment
	@echo "🔧 Setting up OWLS Q4 environment..."
	cd src/fargate && uv sync
	@echo "✅ Environment ready"

run: setup  ## Generate complete analysis (metrics + visualizations)
	@echo "🚀 Running complete Q4 analysis..."
	cd src/fargate && \
	docker build -t owls-q4-scientific:latest . && \
	docker run -v "$$(pwd):/data" -w /data --entrypoint="" owls-q4-scientific:latest uv run python test_embeddings.py
	@echo "✅ Analysis complete - check src/fargate/test_output/"

plots: run  ## Generate visualizations and copy to images/
	@echo "🎨 Copying visualizations to images/..."
	cp src/fargate/test_output/*.png images/ 2>/dev/null || true
	cp src/fargate/test_output/*.json images/ 2>/dev/null || true
	cp src/fargate/test_output/*.txt images/ 2>/dev/null || true
	@echo "✅ Visualizations updated in images/"

test:  ## Run mathematical property tests
	@echo "🧪 Running Q4 property tests..."
	cd src/fargate && \
	docker run -v "$$(pwd):/data" -w /data --entrypoint="" owls-q4-scientific:latest uv run python -m pytest tests/ -v
	@echo "✅ Tests complete"

reproduce:  ## Full reproduction of README results
	@echo "📊 Reproducing all README results..."
	@make clean
	@make plots
	@echo ""
	@echo "🎯 Results Summary:"
	@echo "=================="
	@cat images/qstudy_summary.txt 2>/dev/null || echo "Run 'make plots' first"
	@echo ""
	@echo "📁 Generated files:"
	@ls -la images/*.png images/*.json 2>/dev/null || echo "No files generated yet"

clean:  ## Clean generated files
	@echo "🧹 Cleaning generated files..."
	rm -rf src/fargate/test_output/
	rm -f images/qstudy_*.png images/qstudy_*.json images/qstudy_*.txt
	@echo "✅ Cleaned"

# Development targets
dev-setup: setup  ## Setup development environment with testing tools
	cd src/fargate && uv add --dev pytest hypothesis ruff black mypy

lint:  ## Run code quality checks
	cd src/fargate && uv run ruff check . && uv run black --check .

format:  ## Format code
	cd src/fargate && uv run black . && uv run ruff --fix .

# Docker targets
docker-build:  ## Build Docker container
	cd src/fargate && docker build -t owls-q4-scientific:latest .

docker-shell:  ## Interactive shell in container
	cd src/fargate && docker run -it -v "$$(pwd):/data" -w /data owls-q4-scientific:latest bash

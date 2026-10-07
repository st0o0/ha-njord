PROTO_SRC = protos
PROTO_OUT = custom_components/njord/proto
DOCKER_IMAGE = python:3.12-slim

.PHONY: proto test lint requirements

proto:
	docker run --rm -v "$(CURDIR):/work" -w /work $(DOCKER_IMAGE) \
		sh -c "pip install --quiet 'grpcio-tools>=1.70,<1.79' 'protobuf>=5.0,<6.0' && \
		python -m grpc_tools.protoc \
			-I$(PROTO_SRC) \
			--python_out=$(PROTO_OUT) \
			--grpc_python_out=$(PROTO_OUT) \
			$(PROTO_SRC)/njord/v2/common.proto \
			$(PROTO_SRC)/njord/v2/weather.proto \
			$(PROTO_SRC)/njord/v2/admin.proto \
			$(PROTO_SRC)/njord/v2/ops.proto \
			$(PROTO_SRC)/njord/v2/sensor.proto"

# Runs in Docker: pytest-homeassistant-custom-component needs Python <3.13,
# and its event-loop fixtures assume a Unix event loop (break under native
# Windows pytest even with a 3.12 interpreter). UV_PROJECT_ENVIRONMENT keeps
# the venv off the bind mount — on it, installing/reading homeassistant's
# thousands of files through a Windows volume makes the run hang for minutes.
test:
	docker run --rm -v "$(CURDIR):/work" -w /work -e UV_PROJECT_ENVIRONMENT=/opt/venv $(DOCKER_IMAGE) \
		sh -c "pip install --quiet uv && uv sync --locked --all-extras && uv run pytest tests/ -v"

lint:
	docker run --rm -v "$(CURDIR):/work" -w /work -e UV_PROJECT_ENVIRONMENT=/opt/venv $(DOCKER_IMAGE) \
		sh -c "pip install --quiet uv && uv sync --locked --all-extras && \
		uv run ruff format --check . && uv run ruff check ."

# requirements.txt is the shipped-only footprint (no dev extra) that Trivy
# scans instead of uv.lock, which also resolves the homeassistant test
# dependency's full tree. Regenerate after changing [project.dependencies].
requirements:
	uv export --no-hashes --no-header -o requirements.txt

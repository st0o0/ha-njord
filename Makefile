PROTO_SRC = protos
PROTO_OUT = custom_components/njord/proto
DOCKER_IMAGE = python:3.12-slim

.PHONY: proto test

proto:
	docker run --rm -v "$(CURDIR):/work" -w /work $(DOCKER_IMAGE) \
		sh -c "pip install --quiet grpcio-tools && \
		python -m grpc_tools.protoc \
			-I$(PROTO_SRC) \
			--python_out=$(PROTO_OUT) \
			--grpc_python_out=$(PROTO_OUT) \
			$(PROTO_SRC)/njord/v1/forecast_service.proto \
			$(PROTO_SRC)/njord/v1/config_service.proto"

test:
	docker run --rm -v "$(CURDIR):/work" -w /work $(DOCKER_IMAGE) \
		sh -c "pip install --quiet grpcio protobuf pytest && \
		python -m pytest tests/ -v"

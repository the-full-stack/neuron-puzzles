# TODO: .env.example

# provide ENV=dev to use .env.dev instead of .env
# and to work in the Pulumi dev stack
ENV_LOADED :=
ifeq ($(ENV), dev)
    ifneq (,$(wildcard ./.env.dev))
        include .env.dev
        export
				ENV_LOADED := Loaded config from .env.dev
    endif
else
    ifneq (,$(wildcard ./.env))
        include .env
        export
				ENV_LOADED := Loaded config from .env
    endif
endif

.PHONY: help
.DEFAULT_GOAL := help

help: banner ## get a list of all the targets, plus short descriptions
	@# source for the incantation: https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | awk 'BEGIN {FS = ":.*?##"}; {printf "\033[36m%-12s\033[0m %s\n", $$1, $$2}'

it-all: puzzle-store app ## runs all automated steps to get the application up and running

app: secrets ## deploy the application on Modal
	$(if $(filter dev, $(value ENV)),modal serve app/go.py, \
                modal deploy app/go.py)

puzzle-store: environment secrets ## adds puzzles to a MongoDB collection
	modal run app/data/puzzles.py --json-file start-puzzles.json

secrets: modal-auth ## pushes secrets from .env to Modal
	@$(if $(value MONGODB_USER),, \
		$(error MONGODB_USER is not set. Please set it before running this target.))
	@$(if $(value MONGODB_PASSWORD),, \
		$(error MONGODB_PASSWORD is not set. Please set it before running this target.))
	@$(if $(value MONGODB_HOST),, \
		$(error MONGODB_HOST is not set. Please set it before running this target.))
	@modal secret create mongodb-neuron-puzzles \
		MONGODB_USER=$(MONGODB_USER) MONGODB_PASSWORD=$(MONGODB_PASSWORD) \
		MONGODB_HOST=$(MONGODB_HOST) MONGODB_DBNAME=$(MONGODB_DBNAME)
	@modal secret create neuron-puzzles-api-keys \
		API_KEYS=$(API_KEYS)

modal-auth: environment ## authenticates to Modal
	@$(if $(value MODAL_TOKEN_ID),, \
		$(error MODAL_TOKEN_ID is not set. Please set it before running this target.))
	@$(if $(value MODAL_TOKEN_SECRET),, \
		$(error MODAL_TOKEN_SECRET is not set. Please set it before running this target.))
	@modal token set --token-id $(MODAL_TOKEN_ID) --token-secret $(MODAL_TOKEN_SECRET)

modal-token: environment ## creates token ID and secret for authentication with modal
	modal token new
	@echo "###"
	@echo "# 🧠🧩: Copy the token info from the file mentioned above into a .env file"
	@echo "###"

environment: ## installs required environment for deployment
	@if [ -z "$(ENV_LOADED)" ]; then \
        echo "Error: Configuration file not found"; \
    else \
				echo "###"; \
				echo "# 🧠🧩: $(ENV_LOADED)"; \
				echo "###"; \
	fi
	python -m pip install -qqq -r app/requirements.txt

dev-environment: environment ## installs required environment for development
	python -m pip install -qqq -r app/requirements-dev.txt
	pre-commit install
	npm install -D

banner: ## prints the logo and title in the terminal
	@cat static/assets/logo.txt
	@echo "$$(cat static/assets/title.txt)"

readme: ## generates the README.md file
	@echo "\`\`\`bash" > README.md
	@echo "$$(cat static/assets/title.txt | tail -n +2 | head -n 11)" >> README.md
	@echo "\`\`\`" >> README.md
	@cat .RAWREADME.md >> README.md

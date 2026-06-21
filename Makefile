up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f backend

pipeline-zones:
	docker compose exec backend python -m pipeline.load_zones

pipeline-all:
	docker compose exec backend python -m pipeline.run_pipeline

pipeline-seed:
	docker compose exec backend python -m pipeline.seed_dims

pipeline-trips:
	docker compose exec backend python -m pipeline.load_trips

pipeline-lookup:
	docker compose exec backend python -m pipeline.load_lookup

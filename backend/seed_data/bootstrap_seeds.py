"""Bootstrap seed data only when the local dataset is not ready yet."""

from seed_data.load_seeds import (
    _print_seed_counts,
    collect_seed_counts,
    run_seed_pipeline,
    seed_dataset_ready,
)


def bootstrap_seeds() -> None:
    counts = collect_seed_counts()

    if seed_dataset_ready(counts):
        print("Seed bootstrap skipped: dataset already present.")
        _print_seed_counts(counts)
        return

    print("Seed bootstrap starting: missing or partial dataset detected.")
    _print_seed_counts(counts)
    print()
    run_seed_pipeline()


if __name__ == "__main__":
    bootstrap_seeds()

from typing import Any, Dict, Iterator, List, Tuple

import torch
from jaxtyping import Float
from torch.utils.data import IterableDataset

from synthetic_languages.process.process import Process
from synthetic_languages.process.processes import PROCESS_REGISTRY

# TODO: Create a custom dataloader so you don't have to import the collate_function
#     everywehre
# TODO: Assert they are in the correct vocabulary
# TODO: Make the dataset parallel distributed (??)
# TODO: Figure out the device allocation for batching
# TODO: Test the ProcessDataset __iter__ for robustness against StopIter


class ProcessDataset(IterableDataset):
    # TODO(Adriano)
    # samples: Iterable[int]
    # process_params: Dict[str, float]
    # sequence_length: int
    # num_samples: int

    def __init__(
        self,
        process_name: str,
        process_params: Dict[str, float],
        sequence_length: int,
        num_samples: int,
    ):
        super(ProcessDataset).__init__()

        process_class = PROCESS_REGISTRY.get(process_name, None)
        if process_class is None:
            raise ValueError(
                f"{process_name} is not a recognized process. "
                + f"It must be one of the following {PROCESS_REGISTRY.keys()}"
            )
        process: Process = process_class(**process_params)

        self.samples: Iterator[int] = process.yield_emissions(
            sequence_len=num_samples * (sequence_length + 1)
        )
        self.sequence_length = sequence_length
        self.num_samples = num_samples

    def __len__(self):
        return self.num_samples

    def __iter__(self, sentinel: Any = None) -> Iterator[Tuple[List[int], List[int]]]:
        for _ in range(self.num_samples):
            process_history = [
                next(self.samples) for _ in range(self.sequence_length + 1)
            ]
            yield (process_history[:-1], process_history[1:])


def process_dataset_collate_fn(
    batch: List[Tuple[List[int], List[int]]],
) -> Tuple[
    Float[torch.Tensor, "batch_size sequence_length"],
    Float[torch.Tensor, "batch_size sequence_length"],
]:
    data = [x[0] for x in batch]
    labels = [x[1] for x in batch]
    return torch.tensor(data, dtype=torch.long), torch.tensor(labels, dtype=torch.long)

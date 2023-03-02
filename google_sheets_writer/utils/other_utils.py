from typing import Optional, List, Union


def chunk_list(
    iter_obj: List,
    chunk_size: Optional[int] = 1000,
) -> Union[List, List[List]]:
    """
    Given a list of values, this function will return a list-of-lists
    where the length of the inner lists is equal to the provided chunk size.
    """

    if chunk_size is None:
        return iter_obj

    elif len(iter_obj) <= chunk_size:
        return [iter_obj]

    else:
        chunked_iter = [iter_obj[x:x+chunk_size] for x in range(0, len(iter_obj), chunk_size)]
        return chunked_iter

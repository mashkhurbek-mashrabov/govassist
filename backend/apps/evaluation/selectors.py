import uuid

from apps.evaluation.models import EvalRun


def get_run(ref: str) -> EvalRun:
    """A run by UUID, or the newest run with that name (names are not unique).

    Args:
        ref: A run id or run name.

    Returns:
        The run.

    Raises:
        EvalRun.DoesNotExist: When nothing matches.
    """
    try:
        run_id = uuid.UUID(ref)
    except ValueError:
        run = EvalRun.objects.filter(name=ref).order_by("-created_at").first()
    else:
        run = EvalRun.objects.filter(id=run_id).first()
    if run is None:
        msg = f"No evaluation run {ref!r}."
        raise EvalRun.DoesNotExist(msg)
    return run

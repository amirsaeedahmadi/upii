from django.db import transaction


def delay(signature, countdown=0, *, on_commit=True, **kwargs):
    if on_commit:
        return transaction.on_commit(
            lambda: signature.apply_async(countdown=countdown, **kwargs)
        )

    return signature.apply_async(countdown=countdown, **kwargs)

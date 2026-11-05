from app.models.application import Application


ALLOWED_PRE_APPROVAL_STATUSES = {
    "draft",
}

def request_human_approval(application: Application) -> Application:
    if application.status not in ALLOWED_PRE_APPROVAL_STATUSES:
        raise ValueError(
            "Only draft applications can be sent for human approval."
        )

    application.status = "pending_approval"
    application.status_note = (
        "Waiting for the user's review and approval."
    )

    return application


def approve_application(application: Application) -> Application:
    if application.status != "pending_approval":
        raise ValueError(
            "Only applications waiting for approval can be approved."
        )

    application.status = "ready_for_review"
    application.status_note = (
        "User approved this application. It is ready for the authorized "
        "submission workflow."
    )

    return application


def reject_application(
    application: Application,
    reason: str,
) -> Application:
    if application.status != "pending_approval":
        raise ValueError(
            "Only applications waiting for approval can be rejected."
        )

    application.status = "rejected"
    application.status_note = reason.strip() or "Rejected by the user."

    return application
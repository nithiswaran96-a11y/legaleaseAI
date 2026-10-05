from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from fastapi.responses import Response

from backend.config import settings

from backend.schemas import (
    DocumentRequest,
    ExportRequest,
    GeneratedDocument,
)

from backend.services.document_export import (
    filename_for,
    format_docx,
    format_pdf,
    format_txt,
)

from backend.services.gemini_generator import (
    GeminiDocumentGenerator,
)


router = APIRouter()


def check_length(
    *values: str
) -> None:

    total_length = sum(
        len(value)
        for value in values
    )

    if total_length > settings.max_input_length:

        raise HTTPException(

            status_code=413,

            detail=(
                "Input is too large."
            ),
        )


@router.post(
    "/generate",
    response_model=GeneratedDocument
)
def generate_document(
    request: DocumentRequest
):

    check_length(

        request.document_type,

        request.parties,

        request.terms,

        request.effective_date,
    )

    try:

        generator = (
            GeminiDocumentGenerator()
        )

        content = (
            generator.generate_document(

                document_type=(
                    request.document_type
                ),

                parties=(
                    request.parties
                ),

                terms=(
                    request.terms
                ),

                effective_date=(
                    request.effective_date
                ),
            )
        )

        return GeneratedDocument(

            document_type=(
                request.document_type
            ),

            content=content,

            model=settings.gemini_model,
        )

    except RuntimeError as error:

        raise HTTPException(

            status_code=500,

            detail=str(error),
        ) from error

    except Exception as error:

        raise HTTPException(

            status_code=502,

            detail=(
                f"AI generation failed: "
                f"{error}"
            ),
        ) from error


@router.post(
    "/export/txt"
)
def export_txt(
    request: ExportRequest
):

    content = format_txt(
        request.content
    )

    filename = filename_for(
        request.document_type,
        "txt"
    )

    return Response(

        content=content,

        media_type=(
            "text/plain; charset=utf-8"
        ),

        headers={

            "Content-Disposition":
                f'attachment; filename="{filename}"'
        },
    )


@router.post(
    "/export/docx"
)
async def export_docx(

    document_type: str = Form(...),

    content: str = Form(...),

    logo: UploadFile | None = File(
        default=None
    ),
):

    logo_bytes = None

    if logo:

        logo_bytes = await logo.read()

    document = format_docx(

        text=content,

        document_type=document_type,

        logo_bytes=logo_bytes,
    )

    filename = filename_for(
        document_type,
        "docx"
    )

    return Response(

        content=document,

        media_type=(
            "application/"
            "vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),

        headers={

            "Content-Disposition":
                f'attachment; filename="{filename}"'
        },
    )


@router.post(
    "/export/pdf"
)
async def export_pdf(

    document_type: str = Form(...),

    content: str = Form(...),

    logo: UploadFile | None = File(
        default=None
    ),
):

    logo_bytes = None

    if logo:

        logo_bytes = await logo.read()

    document = format_pdf(

        text=content,

        document_type=document_type,

        logo_bytes=logo_bytes,
    )

    filename = filename_for(
        document_type,
        "pdf"
    )

    return Response(

        content=document,

        media_type="application/pdf",

        headers={

            "Content-Disposition":
                f'attachment; filename="{filename}"'
        },
    )
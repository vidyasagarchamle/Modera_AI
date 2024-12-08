from fastapi import APIRouter, HTTPException, status
from app.schemas.moderation import HTMLContent, ModerationResponse
from app.core.moderator import ContentModerator

router = APIRouter()
moderator = ContentModerator()

@router.post("/moderate", 
            response_model=ModerationResponse,
            status_code=status.HTTP_200_OK,
            summary="Moderate HTML content",
            description="Analyzes HTML content for inappropriate content using GPT-4")
async def moderate_content(content: HTMLContent):
    try:
        if not content.content.strip():
            raise ValueError("HTML content cannot be empty")
            
        result = moderator.moderate_content(content.content)
        return ModerationResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during content moderation: {str(e)}"
        ) 
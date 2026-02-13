"""Repository synchronization routes for ZONE-GPT Core API."""
import os
import subprocess
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/repo", tags=["repository"])


class RepoSyncResponse(BaseModel):
    """Response model for repository sync endpoint."""
    status: str
    commit_sha: str


@router.post("/sync", response_model=RepoSyncResponse)
async def sync_repository():
    """
    Synchronize repository and return current commit SHA.
    
    Returns:
        RepoSyncResponse: Status and current commit SHA
        
    Raises:
        HTTPException: If git command fails
    """
    try:
        # Get the repository path dynamically
        repo_path = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)
        )))

        # Get current commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_path
        )
        commit_sha = result.stdout.strip()

        return RepoSyncResponse(
            status="ok",
            commit_sha=commit_sha
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get commit SHA: {e.stderr}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        ) from e

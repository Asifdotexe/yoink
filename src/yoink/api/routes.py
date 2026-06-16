from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import io
import zipfile
from pathlib import Path
import tempfile

from yoink.core.shredder import shred_code
from yoink.core.shield import mask_secrets, strip_compliance
from yoink.core.packer import pack_codebase
from yoink.core.scanner import get_files_to_process

router = APIRouter(prefix="/api/v1")

class FileInput(BaseModel):
    path: str
    content: str

class PackRequest(BaseModel):
    files: List[FileInput]
    strip_comments: Optional[bool] = True
    strip_whitespace: Optional[bool] = True
    mask_secrets: Optional[bool] = True
    custom_secrets: Optional[Dict[str, str]] = None
    compliance_patterns: Optional[Dict[str, str]] = None
    visualize: Optional[bool] = True

class PackResponse(BaseModel):
    total_files: int
    packed_content: str

class SanitizeRequest(BaseModel):
    content: str
    file_extension: str = ".py"
    strip_comments: bool = True
    strip_whitespace: bool = True
    mask_secrets: bool = True
    custom_secrets: Optional[Dict[str, str]] = None
    compliance_patterns: Optional[Dict[str, str]] = None

class SanitizeResponse(BaseModel):
    sanitized_content: str

@router.post("/sanitize", response_model=SanitizeResponse)
async def sanitize_content(request: SanitizeRequest):
    """
    Sanitize a single file's content (stripping comments/whitespace and masking secrets).
    """
    content = request.content
    content = shred_code(content, request.file_extension, request.strip_comments, request.strip_whitespace)
    
    if request.mask_secrets:
        content = mask_secrets(content, request.custom_secrets)
        
    if request.compliance_patterns:
        content = strip_compliance(content, request.compliance_patterns)
        
    return SanitizeResponse(sanitized_content=content)

@router.post("/pack", response_model=PackResponse)
async def pack_files(request: PackRequest):
    """
    Pack a list of file paths and contents directly.
    Useful for frontends or editor plugins that have the files already in memory.
    """
    if not request.files:
        raise HTTPException(status_code=400, detail="No files provided.")
        
    # Write files to a temporary directory to reuse packer
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        file_paths = []
        for file_input in request.files:
            file_path = temp_path / file_input.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_input.content)
            file_paths.append(file_path)
            
        packed_md = pack_codebase(
            root_dir=temp_path,
            files=file_paths,
            strip_comments=request.strip_comments,
            strip_whitespace=request.strip_whitespace,
            mask_sensitive=request.mask_secrets,
            custom_secrets=request.custom_secrets,
            compliance_patterns=request.compliance_patterns,
            visualize=request.visualize
        )
        
        return PackResponse(
            total_files=len(file_paths),
            packed_content=packed_md
        )

@router.post("/pack-zip", response_model=PackResponse)
async def pack_zip(
    zip_file: UploadFile = File(...),
    strip_comments: bool = Form(True),
    strip_whitespace: bool = Form(True),
    mask_secrets: bool = Form(True),
    visualize: bool = Form(True)
):
    """
    Upload a zip file containing a codebase and receive a packed markdown file.
    """
    if not zip_file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a zip archive.")
        
    contents = await zip_file.read()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        try:
            with zipfile.ZipFile(io.BytesIO(contents)) as z:
                z.extractall(temp_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid zip file: {e}")
            
        # Read .yoinkconfig.json inside the zip if present to align scanner/compliance configurations
        # ponytail: simplified configuration loading to avoid file context managers and redundant variable initializations.
        # Why: We load config via json.loads and read_text using a fallback empty dictionary. This keeps variables clean and defaults to None if the keys are absent, avoiding multi-line variable declarations.
        archive_config_file, archive_configuration = temp_path / ".yoinkconfig.json", {}
        if archive_config_file.exists():
            import json
            try:
                archive_configuration = json.loads(archive_config_file.read_text(encoding="utf-8"))
            except Exception:
                pass
                
        compliance_patterns = archive_configuration.get("compliance_patterns", None)
        custom_secrets = archive_configuration.get("secret_patterns", None)
        exclude_patterns = archive_configuration.get("exclude_patterns", None)
        include_extensions = archive_configuration.get("include_extensions", None)
                
        files = get_files_to_process(temp_path, exclude_patterns, include_extensions)
        if not files:
            raise HTTPException(status_code=400, detail="No valid text files found in the zip archive.")
            
        packed_md = pack_codebase(
            root_dir=temp_path,
            files=files,
            strip_comments=strip_comments,
            strip_whitespace=strip_whitespace,
            mask_sensitive=mask_secrets,
            custom_secrets=custom_secrets,
            compliance_patterns=compliance_patterns,
            visualize=visualize
        )
        
        return PackResponse(
            total_files=len(files),
            packed_content=packed_md
        )
